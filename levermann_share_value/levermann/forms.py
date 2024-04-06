from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.datetime import DateField
from wtforms.validators import DataRequired


class SearchFrom(FlaskForm):
    isin = StringField('isin', validators=[DataRequired()])
    submit = SubmitField('search')
