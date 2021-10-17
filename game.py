import sqlite3
import math
import random
import os

from discord.ext import commands
from logger import console_log

# ==== methods =====
# game.register(uid)
# game.work(uid, multiplier)
# game.rob(author_id, target_id, multiplier)
# game.donate(author_id, target_id, amount, multiplier)
# game.charity(uid, amount, multiplier)
# game.gamble(uid, amount, multiplier)
# game.buy_work(uid, amount)
# game.buy_rob(uid, amount)
# game.use_work_charge(uid, amount)
# game.use_rob_charge(uid, amount)
# game.withdraw(uid, amount)
# game.deposit(uid, amount)
# game.transfer(author_id, target_id, amount)

# define exceptions
class GameExceptions:
    class UserNotFound(commands.CommandError):
        """Could not find user in database"""
        pass

    class InvalidAmount(commands.CommandError):
        """Amount specified is invalid"""
        pass

    class InvalidRobTarget(commands.CommandError):
        """Cannot rob user with zero cash"""
        pass

    class NotEnoughCash(commands.CommandError):
        """Insufficient cash"""
        pass

    class InsufficientBankBalance(commands.CommandError):
        """Insufficient bank balance"""
        pass

class Game:
    def __init__(self, db):
        # init dir
        if not os.path.exists('saves'):
            os.mkdir('saves')

        # init db
        path_to_db = f'./saves/{db}.db'

        self.conn = sqlite3.connect(path_to_db)
        self.c = self.conn.cursor()

        # init tables
        with self.conn:
            self.c.execute("CREATE TABLE IF NOT EXISTS users (uid INTEGER, level INTEGER, exp INTEGER, cash INTEGER)")
            self.c.execute("CREATE TABLE IF NOT EXISTS perks (uid INTEGER, rob INTEGER, work INTEGER)")
            self.c.execute("CREATE TABLE IF NOT EXISTS banks (uid INTEGER, balance INTEGER)")

    def register(self, uid):
        user = User(uid)
        user = user.register(self.conn, self.c)
        return user

    def work(self, uid, multiplier=1):
        user = User.get(self.conn, self.c, uid)
        user.perks = Perk.get(self.conn, self.c, uid)

        # ensure argument type
        multiplier = float(multiplier)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")

        has_perk = self.use_work_charge(uid)

        if has_perk:
            multiplier = multiplier + 1

        amount = round(random.randint(user.level, user.level * 3) * multiplier)
        
        cash = user.add_cash(self.conn, self.c, amount)
        exp, levelup = user.add_exp(self.conn, self.c, multiplier)

        return {"amount": amount, "cash": cash, "exp": exp, "levelup": levelup, "perk": has_perk}

    def rob(self, author_id, target_id, multiplier=0.9):
        user = User.get(self.conn, self.c, author_id)
        target = User.get(self.conn, self.c, target_id)

        # ensure argument type
        multiplier = float(multiplier)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")
        if not target:
            raise GameExceptions.UserNotFound("User is not registered.")
        if target.cash <= 0:
            raise GameExceptions.InvalidRobTarget("This person has nothing you can take")

        has_perk = self.use_rob_charge(author_id)

        amount = round(random.randint(1, round(target.cash * 0.20)) * multiplier)
        x = random.randint(0, 100)

        if has_perk:
            x = x - 15

        if x > 49:
            user.take_cash(self.conn, self.c, amount)
            failed = True
            exp = 0
            levelup = False
        else:
            user.add_cash(self.conn, self.c, amount)
            exp, levelup = user.add_exp(self.conn, self.c, multiplier)
    
            target.take_cash(self.conn, self.c, amount)
            failed = False

        user = user.get(self.conn, self.c, author_id)
        cash = user.cash

        console_log(f"Command 'rob' called. Return value: {x}")

        return {"failed": failed, "amount": amount, "cash": cash, "exp": exp, "levelup": levelup, "perk": has_perk}

    def donate(self, author_id, target_id, amount, multiplier=1):
        user = User.get(self.conn, self.c, author_id)
        target = User.get(self.conn, self.c, target_id)

        # ensure argument type
        amount = int(amount)
        multiplier = float(multiplier)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")
        if not target:
            raise GameExceptions.UserNotFound("User is not registered.")
        if amount > user.cash or amount <= 0:
            raise GameExceptions.InvalidAmount("Amount specified exceeds available cash or is zero.")

        cash = user.take_cash(self.conn, self.c, amount)
        exp, levelup = user.add_exp(self.conn, self.c, multiplier, amount)

        cash = target.add_cash(self.conn, self.c, amount)
        
        return {"amount": amount, "cash": cash, "exp": exp, "levelup": levelup}

    def charity(self, uid, amount, multiplier=0.9):
        user = User.get(self.conn, self.c, uid)

        # ensure argument type
        amount = int(amount)
        multiplier = float(multiplier)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")
        if amount > user.cash or amount < 0:
            raise GameExceptions.InvalidAmount("Amount specified exceeds available cash or is zero.")

        cash = user.take_cash(self.conn, self.c, amount)
        exp, levelup = user.add_exp(self.conn, self.c, multiplier, amount)

        return {"cash": cash, "exp": exp, "levelup": levelup}

    def gamble(self, uid, amount, multiplier=1):
        user = User.get(self.conn, self.c, uid)

        # ensure argument type
        amount = int(amount)
        multiplier = float(multiplier)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")
        if amount > user.cash or amount < 0:
            raise GameExceptions.InvalidAmount("Amount specified exceeds available cash or is zero.")

        # limits
        lower_limit = round(amount * 0.1)
        upper_limit = round(amount * 2.0)

        value = random.randint(lower_limit, upper_limit)
        win_value = random.randint(0, 100)

        if win_value > 49:
            cash = user.add_cash(self.conn, self.c, value)
            win = True
        else:
            cash = user.take_cash(self.conn, self.c, value)
            win = False

        return {"amount": value, "cash": cash, "win": win}

    def buy_work(self, uid, amount):
        # work price:
        price = 10

        user = User.get(self.conn, self.c, uid)

        # esnure data type
        amount = int(amount)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")

        user.perks = Perk.get(self.conn, self.c, uid)

        cost = amount * price
        if cost > user.cash:
            raise GameExceptions.NotEnoughCash("You cannot afford this.")
        
        user.take_cash(self.conn, self.c, cost)
        user.perks.add_work_charge(self.conn, self.c, amount)
        return {"amount": amount, "cost": cost}

    def buy_rob(self, uid, amount):
        # rob price:
        price = 50

        user = User.get(self.conn, self.c, uid)

        # esnure data type
        amount = int(amount)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")

        user.perks = Perk.get(self.conn, self.c, uid)

        cost = amount * price
        if cost > user.cash:
            raise GameExceptions.NotEnoughCash("You cannot afford this.")
        
        user.take_cash(self.conn, self.c, cost)
        user.perks.add_rob_charge(self.conn, self.c, amount)
        return {"amount": amount, "cost": cost}

    def use_work_charge(self, uid, amount=1):
        user = User.get(self.conn, self.c, uid)

        amount = int(amount)

        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")

        user.perk = Perk.get(self.conn, self.c, uid)

        if user.perk.work < amount:
            return False
        
        user.perk.take_work_charge(self.conn, self.c, amount)
        return True

    def use_rob_charge(self, uid, amount=1):
        user = User.get(self.conn, self.c, uid)

        amount = int(amount)

        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")

        user.perk = Perk.get(self.conn, self.c, uid)

        if user.perk.rob < amount:
            return False

        user.perk.take_rob_charge(self.conn, self.c, amount)
        return True

    def deposit(self, uid, amount):
        user = User.get(self.conn, self.c, uid)
        user.bank = Bank.get(self.conn, self.c, uid)

        amount = int(amount)

        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")
        if amount > user.cash:
            raise GameExceptions.NotEnoughCash("You dont have enough cash.")

        user.take_cash(self.conn, self.c, amount)
        user.bank.deposit(self.conn, self.c, amount)

        return amount

    def withdraw(self, uid, amount):
        user = User.get(self.conn, self.c, uid)
        user.bank = Bank.get(self.conn, self.c, uid)

        amount = int(amount)

        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")
        if amount > user.bank.balance:
            raise GameExceptions.InsufficientBankBalance("You do not have enough cash in the bank.")

        user.add_cash(self.conn, self.c, amount)
        user.bank.withdraw(self.conn, self.c, amount)

        return amount

    def transfer(self, author_id, target_id, amount):
        user = User.get(self.conn, self.c, author_id)
        user.bank = Bank.get(self.conn, self.c, author_id)

        target = User.get(self.conn, self.c, target_id)
        target.bank = Bank.get(self.conn, self.c, target_id)

        amount = int(amount)

        if not user or not target:
            raise GameExceptions.UserNotFound("You must be registered to do this.")
        if amount > user.bank.balance:
            raise GameExceptions.InsufficientBankBalance("You do not have enough cash in the bank.")

        user.bank.withdraw(self.conn, self.c, amount)
        target.bank.deposit(self.conn, self.c, amount)

        return amount

class User:
    def __init__(self, uid, level=1, exp=0, cash=0):
        # user.property
        self.uid = uid
        self.level = level
        self.exp = exp
        self.cash = cash

    @property
    def exp_to_levelup(self):
        value = (self.level ** 2) + (self.level * 2) + 2
        return value

    @classmethod
    def instance(cls, data):
        return cls(*data)

    @classmethod
    def get(cls, conn, c, uid):
        with conn:
            c.execute("SELECT * FROM users WHERE uid=:uid", {"uid": uid})
            data = c.fetchone()
            if data:
                return cls.instance(data)

    def register(self, conn, c):
        with conn:
            # proceed only when unique uid            
            if not self.get(conn, c, self.uid):
                c.execute("INSERT INTO users VALUES (:uid, :level, :exp, :cash)", {
                    "uid": int(self.uid),
                    "level": int(self.level),
                    "exp": int(self.exp),
                    "cash": int(self.cash)
                })
                return self.get(conn, c, self.uid)

    def update(self, conn, c):
        with conn:
            # proceed only when existent user
            if self.get(conn, c, self.uid):
                c.execute("UPDATE users SET level=:level, exp=:exp, cash=:cash WHERE uid=:uid", {
                    "level": int(self.level),
                    "exp": int(self.exp),
                    "cash": int(self.cash),
                    "uid": int(self.uid)
                })

    def take_cash(self, conn, c, amount: int):
        self.cash = self.cash - amount
        self.update(conn, c)
        return self.cash

    def add_cash(self, conn, c, amount: int):
        self.cash = self.cash + amount
        self.update(conn, c)
        return self.cash

    def set_cash(self, conn, c, amount: int):
        self.cash = amount
        self.update(conn, c)
        return self.cash

    def add_exp(self, conn, c, multiplier, override_value=None):
        base = math.log(override_value, 1.1) if override_value else self.level
        upper_limit = round(1 + base * 2 * multiplier)
        lower_limit = 0 if override_value else self.level
        amount = random.randint(lower_limit, upper_limit)
        self.exp = self.exp + amount

        if self.exp > self.exp_to_levelup:
            levelup = True

            while self.exp > self.exp_to_levelup:
                max_exp = self.exp_to_levelup
                self.exp = self.exp = max_exp
                self.level = self.level + 1
        else:
            levelup = False

        self.update(conn, c)
        return amount, levelup

    def set_exp(self, conn, c, amount: int):
        self.exp = amount
        self.update(conn, c)
        return self.exp

    def set_level(self, conn, c, amount: int):
        self.level = amount
        self.update(conn, c)
        return self.level

class Perk:
    def __init__(self, uid, work=0, rob=0):
        self.uid = uid
        self.work = work
        self.rob = rob

    @property
    def data(self):
        return self.__dict__

    @classmethod
    def instance(cls, data):
        return cls(*data)

    def new(self, conn, c):
        with conn:
            c.execute("SELECT * FROM perks WHERE uid=:uid", {"uid": self.uid})
            data = c.fetchone()
            if not data:
                c.execute("INSERT INTO perks VALUES (:uid, :work, :rob)", {
                    "uid": self.uid,
                    "work": self.work,
                    "rob": self.rob
                })

    @classmethod
    def get(cls, conn, c, uid):
        data = None
        while not data:
            with conn:
                c.execute("SELECT * FROM perks WHERE uid=:uid", {"uid": uid})
                data = c.fetchone()
                if data:
                    return cls.instance(data)
                else:
                    perk = Perk(uid)
                    perk.new(conn, c)

    def update(self, conn, c):
        if self.get(conn, c, self.uid):
            with conn:
                c.execute("UPDATE perks SET work=:work, rob=:rob WHERE uid=:uid", {
                    "uid": self.uid,
                    "work": self.work,
                    "rob": self.rob
                })
        return self.get(conn, c, self.uid)

    def add_rob_charge(self, conn, c, amount):
        self.rob = self.rob + amount
        return self.update(conn, c)

    def take_rob_charge(self, conn, c, amount):
        self.rob = self.rob - amount
        return self.update(conn, c)

    def add_work_charge(self, conn, c, amount):
        self.work = self.work + amount
        return self.update(conn, c)

    def take_work_charge(self, conn, c, amount):
        self.work = self.work - amount
        return self.update(conn, c)

class Bank:
    def __init__(self, uid, balance=0):
        self.uid = uid
        self.balance = balance

    @property
    def data(self):
        return self.__dict__

    @classmethod
    def instance(cls, data):
        return cls(*data)

    def new(self, conn, c):
        with conn:
            c.execute("SELECT * FROM banks WHERE uid=:uid", {"uid": self.uid})
            data = c.fetchone()
            if not data:
                c.execute("INSERT INTO banks VALUES (:uid, :balance)", {
                    "uid": self.uid,
                    "balance": self.balance
                })

    @classmethod
    def get(cls, conn, c, uid):
        data = None
        while not data:
            with conn:
                c.execute("SELECT * FROM banks WHERE uid=:uid", {"uid": uid})
                data = c.fetchone()
                if data:
                    return cls.instance(data)
                else:
                    bank = Bank(uid)
                    bank.new(conn, c)

    def update(self, conn, c):
        if self.get(conn, c, self.uid):
            with conn:
                c.execute("UPDATE banks SET balance=:balance WHERE uid=:uid", {
                    "uid": self.uid,
                    "balance": self.balance
                })
        return self.get(conn, c, self.uid)

    def withdraw(self, conn, c, amount):
        self.balance = self.balance - amount
        return self.update(conn, c)

    def deposit(self, conn, c, amount):
        self.balance = self.balance + amount
        return self.update(conn, c)