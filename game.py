import sqlite3
import math
import random
import os

# ==== methods =====
# game.register(uid)
# game.work(uid, multiplier)
# game.rob(author_id, target_id, multiplier)
# game.donate(author_id, target_id, amount, multiplier)
# game.charity(uid, amount, multiplier)

# define exceptions
class UserNotFound(Exception):
    """Could not find user in database"""
    pass

class InvalidAmount(Exception):
    """Amount specified is invalid"""
    pass

class InvalidRobTarget(Exception):
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

        if not user:
            raise UserNotFound

        amount = round(random.randint(user.level, user.level * 3) * multiplier)
        
        cash = user.add_cash(self.conn, self.c, amount)
        exp, levelup = user.add_exp(self.conn, self.c, multiplier)

        return {"amount": amount, "cash": cash, "exp": exp, "levelup": levelup}

    def rob(self, author_id, target_id, multiplier=0.9):
        user = User.get(self.conn, self.c, author_id)
        target = User.get(self.conn, self.c, target_id)

        if not user or not target:
            raise UserNotFound

        if target.cash == 0:
            raise InvalidRobTarget

        amount = round(random.randint(1, target.cash * 0.20) * multiplier)
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

        if not user or not target:
            raise UserNotFound

        if amount > user.cash or amount < 0:
            raise InvalidAmount

        user.take_cash(self.conn, self.c, amount)
        user.add_exp(self.conn, self.c, multiplier)

        target.add_cash(self.conn, self.c, amount)

    def charity(self, uid, amount, multiplier=0.9):
        user = User.get(self.conn, self.c, uid)

        if not user:
            raise UserNotFound

        if amount > user.cash or amount < 0:
            raise InvalidAmount

        user.take_cash(self.conn, self.c, amount)
        user.add_exp(self.conn, self.c, multiplier)

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
                    "uid": self.uid,
                    "level": self.level,
                    "exp": self.exp,
                    "cash": self.cash
                })
                return self.get(conn, c, self.uid)

    def update(self, conn, c):
        with conn:
            # proceed only when existent user
            if self.get(conn, c, self.uid):
                c.execute("UPDATE users SET level=:level, exp=:exp, cash=:cash WHERE uid=:uid", {
                    "level": self.level,
                    "exp": self.exp,
                    "cash": self.cash,
                    "uid": self.uid
                })

    def take_cash(self, conn, c, amount):
        self.cash = self.cash - amount
        self.update(conn, c)
        return self.cash

    def add_cash(self, conn, c, amount):
        self.cash = self.cash + amount
        self.update(conn, c)
        return self.cash

    def set_cash(self, conn, c, amount):
        self.cash = amount
        self.update(conn, c)
        return self.cash

    def add_exp(self, conn, c, multiplier):
        amount = round(1 + self.level * 2 * multiplier)
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

    def set_exp(self, conn, c, amount):
        self.exp = amount
        self.update(conn, c)
        return self.exp

    def set_level(self, conn, c, amount):
        self.level = amount
        self.update(conn, c)
        return self.level