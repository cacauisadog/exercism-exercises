import json


class RestAPI:
    def __init__(self, database: dict = None) -> None:
        self.database = database

    def get(self, url: str, payload: str = None) -> str:
        if url != '/users':
            raise Exception('404 Not Found')

        if not payload:
            users = json.dumps(self.database)
            return users
        else:
            user_list = json.loads(payload).get('users')
            users = _get_users(user_list, self.database)
            return json.dumps({'users': users})

    def post(self, url: str, payload: str = None) -> str:
        if url not in ('/add', '/iou'):
            raise Exception('404 Not Found')
        if not payload:
            raise Exception('400 Bad Request')

        if url == '/add':
            user_params = json.loads(payload)
            user = User(**user_params)
            self.database['users'].append(user.__dict__)
            return user.to_dict_json()

        if url == '/iou':
            lending_params = json.loads(payload)
            users_affected = execute_lending(lending_params, self.database)
            return json.dumps({'users': users_affected})


class User:
    def __init__(self, user: str, owes: dict = {}, owed_by: dict = {}, balance: float = 0.0) -> None:
        self.name = user
        self.owes = owes
        self.owed_by = owed_by
        self.balance = balance

    def to_dict_json(self) -> str:
        duser = {
            'name': self.name,
            'owes': self.owes,
            'owed_by': self.owed_by,
            'balance': self.balance,
        }
        return json.dumps(duser)


def execute_lending(lending_operation: dict, database: dict) -> None:
    users = database['users']
    lender_name = lending_operation['lender']
    borrower_name = lending_operation['borrower']
    amount = lending_operation['amount']

    dlender = next(user for user in users if user['name'] == lender_name)
    dborrower = next(user for user in users if user['name'] == borrower_name)

    lender_owed_by = dlender['owed_by']
    lender_already_owed = lender_owed_by.get(borrower_name, 0)
    lender_borrowed_from = dlender['owes']
    lender_owes_borrower = lender_borrowed_from.get(borrower_name, 0)

    borrower_owes = dborrower['owes']
    borrower_already_owes = borrower_owes.get(lender_name, 0)

    lender_balance = dlender['balance']
    borrower_balance = dborrower['balance']

    if lender_owes_borrower > 0:
        if lender_owes_borrower - amount > 0:
            _update_user_owes(dlender, borrower_name, lender_owes_borrower - amount)
            _update_user_owed_by(dborrower, lender_name, lender_owes_borrower - amount)
        elif lender_owes_borrower - amount < 0:
            dlender['owes'] = {}
            _update_user_owed_by(dlender, borrower_name, abs(lender_owes_borrower - amount))
            dborrower['owed_by'] = {}
            _update_user_owes(dborrower, lender_name, abs(lender_owes_borrower - amount))
        else:
            dlender['owes'] = {}
            dlender['owed_by'] = {}
            dborrower['owed_by'] = {}
            dborrower['owes'] = {}
    else:
        _update_user_owes(dborrower, lender_name, borrower_already_owes + amount)
        _update_user_owed_by(dlender, borrower_name, lender_already_owed + amount)

    dlender.update({'balance': lender_balance + amount})
    dborrower.update({'balance': borrower_balance - amount})

    dlender = _order_duser(dlender)
    dborrower = _order_duser(dborrower)

    return sorted([dlender, dborrower], key=lambda k: k['name'])


def _order_duser(duser: dict) -> dict:
    sorted_owed_by = dict(sorted(duser['owed_by'].items()))
    sorted_owes = dict(sorted(duser['owes'].items()))
    duser['owed_by'] = sorted_owed_by
    duser['owes'] = sorted_owes

    return duser


def _get_users(user_list: list, database: dict) -> list:
    users = []
    for username in user_list:
        duser = next((u for u in database['users'] if u['name'] == username), None)
        if duser:
            users.append(duser)

    return sorted(users, key=lambda k: k['name'])


def _update_user_owes(user: dict, owes: str, amount: float) -> None:
    user['owes'].update({owes: amount})


def _update_user_owed_by(user: dict, owed_by: str, amount: float) -> None:
    user['owed_by'].update({owed_by: amount})
