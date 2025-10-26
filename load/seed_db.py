# load/seed_db.py
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database import models
from datetime import datetime, timedelta

def seed(users_per_group=10, groups=("КС-21","КС-22","КС-23"), days=5):
    if hasattr(models, "init_db"):
        models.init_db()

    # опціонально: якщо є add_user, додай кількох
    if hasattr(models, "add_user"):
        for g in groups:
            for i in range(users_per_group):
                uid = 10_000_000 + (i % 100000)
                try:
                    models.add_user(uid, group_name=g, is_admin=0)
                except Exception:
                    pass

    start = (datetime.today().date() + timedelta(days=1))  # ЗАВТРА, щоб точно не було «прошлих» дат
    subjects = ["Алгебра","Прога","АК","БД","Фізра"]
    rooms = ["101","201","301","401","501"]
    times = ["08:30","10:10","11:50","13:30","15:10"]

    for d in range(days):
        day = (start + timedelta(days=d)).isoformat()
        for g in groups:
            for t, subj, room in zip(times, subjects, rooms):
                try:
                    models.add_event(day, t, subj, room, g)
                except Exception as e:
                    # якщо валідація, просто пропустимо проблемний кейс
                    pass
    print("Seed done")

if __name__ == "__main__":
    seed()
