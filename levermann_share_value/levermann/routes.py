import logging

from flask import render_template, request, Blueprint, flash, redirect, url_for

from levermann_share_value.scraper import scraper_mgr as lsm
from levermann_share_value.levermann.forms import SearchFrom

# TODO - Button for loading share data
# TODO - LInk to page which loads shares from DB
routes = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)


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
