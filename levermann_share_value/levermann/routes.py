from flask import render_template, request, Blueprint, flash, redirect, url_for

from levermann_share_value.levermann.forms import SearchFrom
from levermann_share_value.levermann.levermann_share_mgr import LevermannShareMgr, get_all_shares
from levermann_share_value.database.models import Share
from levermann_share_value import db
import logging

# TODO - Button for loading share data
# TODO - LInk to page which loads shares from DB
routes = Blueprint('routes', __name__)
logger = logging.getLogger(__name__)

scraper_mgr = LevermannShareMgr(db)


@routes.route('/', methods=['GET', 'POST'])
def index():
    form = SearchFrom()
    isin: str = request.args.get('isin')
    if request.method == 'POST' and form.validate_on_submit():
        isin = form.isin.data
        flash(f'Search for {isin}')
        logger.info(f"form for {isin} submitted")
        share: Share = scraper_mgr.scrape_share_by(isin=isin)
        return redirect(url_for('routes.index'))
    elif isin is not None:
        scraper_mgr.scrape_share_by(isin=isin)
    shares: list = get_all_shares()
    return render_template('index.html', shares=shares, form=form)

@routes.route('/all_fingreen')
def get_all_fingreen_share():
    # scraper_mgr.load_everything()
    scraper_mgr.load_ov_data_for_all_shares()
    return redirect(url_for('routes.index'))
