from database import User, Group


def get_user(chat_id, session) -> User:
    user = session.query(User).filter_by(chat_id=chat_id).first()
    return user or None


def get_group(group_id, session) -> Group:
    group = session.query(Group).filter_by(id=group_id).first()
    return group or None
