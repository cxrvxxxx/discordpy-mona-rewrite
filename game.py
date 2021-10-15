import sqlite3
import math
import random
import os

from discord.ext import commands

# ==== methods =====
# game.register(uid)
# game.work(uid, multiplier)
# game.rob(author_id, target_id, multiplier)
# game.donate(author_id, target_id, amount, multiplier)
# game.charity(uid, amount, multiplier)
# game.gamble(uid, amount, multiplier)

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

    def register(self, uid):
        user = User(uid)
        user = user.register(self.conn, self.c)
        return user

    def work(self, uid, multiplier=1):
        user = User.get(self.conn, self.c, uid)

        # ensure argument type
        multiplier = float(multiplier)

        # validation
        if not user:
            raise GameExceptions.UserNotFound("You must be registered to do this.")

        amount = round(random.randint(user.level, user.level * 3) * multiplier)
        
        cash = user.add_cash(self.conn, self.c, amount)
        exp, levelup = user.add_exp(self.conn, self.c, multiplier)

        return {"amount": amount, "cash": cash, "exp": exp, "levelup": levelup}

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

        amount = round(random.randint(1, round(target.cash * 0.20)) * multiplier)
        x = random.randint(0, 9)

        if x > 5:
            cash = user.take_cash(self.conn, self.c, amount)
            failed = True
            exp = 0
            levelup = False
        else:
            cash = user.add_cash(self.conn, self.c, amount)
            exp, levelup = user.add_exp(self.conn, self.c, multiplier)
    
            cash = target.take_cash(self.conn, self.c, amount)
            failed = False

        return {"failed": failed, "amount": amount, "cash": cash, "exp": exp, "levelup": levelup}

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
        if amount > user.cash or amount < 0:
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
        amount = round(1 + base * 2 * multiplier)
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