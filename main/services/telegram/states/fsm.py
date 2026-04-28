from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    first_name = State()
    age        = State()
    region     = State()
    phone      = State()


class CatalogStates(StatesGroup):
    choose_browse_mode = State()
    choose_category    = State()
    choose_subcategory = State()
    choose_product     = State()


class DealerStates(StatesGroup):
    choose_dealer = State()


class TestDriveStates(StatesGroup):
    choose_product = State()
    choose_date    = State()
    choose_time    = State()
    choose_city    = State()
    confirm        = State()


class LeadStates(StatesGroup):
    choose_interest = State()
    confirm         = State()


class LeasingStates(StatesGroup):
    choose_browse_mode  = State()
    choose_category     = State()
    choose_subcategory  = State()
    choose_product      = State()
    choose_down_payment = State()
    choose_term         = State()
    confirm             = State()

