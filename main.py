from db_repo import DbRepo
from db_config import local_session, create_all_entities

repo = DbRepo(local_session)

local_session.execute('drop TABLE customers CASCADE')
local_session.execute('drop TABLE users CASCADE')
local_session.commit()
create_all_entities()
repo.reset_db()

