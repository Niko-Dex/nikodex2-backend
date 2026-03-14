from common import dto, models
from common.models import AccountType


def account_of_type(user: dto.User | models.User, account_type: AccountType):
    return AccountType(user.account_type) == account_type
