from flask import render_template, request, Blueprint, flash, redirect, url_for

from levermann_share_value.levermann.forms import SearchFrom
from levermann_share_value.levermann import levermann_share_mgr as lsm
from levermann_share_value.database.models import Share
import logging

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
        share: Share = lsm.get_share_by_isin(isin)
        return redirect(url_for('routes.index'))
    elif isin is not None:
        lsm.get_share_by_isin(isin)
    shares: list = lsm.get_all_shares()
    return render_template('index.html', shares=shares, form=form)


@routes.route('/all_fingreen')
def get_all_fingreen_share():
    # scraper_mgr.load_everything()
    # lsm.load_everything()
    lsm.load_shares_from_fingreen()
    return redirect(url_for('routes.index'))
