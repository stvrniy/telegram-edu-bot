# load/seed_db.py
from database import models
from datetime import datetime, timedelta

def seed(users_per_group=50, groups=("КС-21","КС-22","КС-23"), days=7):
    models.init_db()
    for g in groups:
        for i in range(users_per_group):
            uid = 10_000_000 + hash((g, i)) % 1_000_000
            models.add_user(uid, group_name=g, is_admin=0)

    start = datetime.today().date()
    subjects = ["Алгебра","Прога","АК","БД","Фізра"]
    rooms = ["101","201","301","401","501"]
    times = ["08:30","10:10","11:50","13:30","15:10"]
    for d in range(days):
        day = (start + timedelta(days=d)).isoformat()
        for g in groups:
            for t, subj, room in zip(times, subjects, rooms):
                models.add_event(day, t, subj, room, g)
    print("Seed done")

if __name__ == "__main__":
    seed()
