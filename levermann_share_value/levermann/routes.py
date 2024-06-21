import logging

from flask import render_template, request, Blueprint, flash, redirect, url_for
from flask_login import login_user, logout_user, current_user, login_required

from levermann_share_value.database.models import User
from levermann_share_value.levermann.forms import SearchFrom
from levermann_share_value.scraper import scraper_mgr as lsm
from levermann_share_value.levermann import constants

# TODO - Button for loading share data
# TODO - LInk to page which loads shares from DB
routes = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

#https://www.youtube.com/watch?v=t9zA1gvrTvo
@routes.route('/login/<uid>')
def login(uid: int):
    user: User = User.query.get(uid)
    print(user)
    login_user(user)
    return 'Successfully logged in!'

@routes.route('/logout')
def logout():
    logout_user()
    return 'Successfully logged out!'

@routes.route('/info', methods=['GET'])
def info():
    if current_user.is_active:
        return str(current_user.username)
    else:
        return 'No User is logged in'

@routes.route('/', methods=['GET', 'POST'])
def index():
    form = SearchFrom()
    isin: str = request.args.get('isin')
    if request.method == 'POST' and form.validate_on_submit():
        isin = form.isin.data
        flash(f'Search for {isin}')
        logger.info(f"form for {isin} submitted")
        lsm.get_share_by_isin(isin)
        return redirect(url_for('routes.index'))
    elif isin is not None:
        lsm.get_share_by_isin(isin)
    shares: list = lsm.get_all_shares()
    return render_template('index.html', shares=shares, form=form)


@routes.route('/get_data', methods=['GET'])
def get_data():
    share_id = request.args.get('share_id')
    fetch_date = request.args.get('fetch_date')
    logger.info(f"get data for {share_id} from {fetch_date}")
    share_data = lsm.get_share_values_for_fetch_date(share_id, fetch_date)
    logger.info(share_data)
    share_data['share_type'] = share_data['share_type'].value
    return share_data


@routes.route('/change_type', methods=['POST'])
def change_type():
    changed_share__type = int(request.form.get('change_type'))
    share_id = int(request.form.get('share_id'))
    logger.info(f'Received: Share ID={share_id}, Change Type={change_type}')
    lsm.change_type(share_id, changed_share__type)
    return redirect(url_for('routes.index'))


# TODO -change to POST
@routes.route('/update_all_shares', methods=['GET'])
def update_all_shares():
    lsm.update_all_shares()


@routes.route('/all')
def get_all_green_share():
    # scraper_mgr.load_everything()
    # lsm.load_everything()
    lsm.load_all_shares()
    return redirect(url_for('routes.index'))


@routes.route('/update_all')
def update_all_green_share():
    # scraper_mgr.load_everything()
    # lsm.load_everything()
    lsm.update_all_shares()
    return redirect(url_for('routes.index'))
