"""Equipment forms for area and equipment management."""

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class AreaCreateForm(FlaskForm):
    """Form for creating a new area."""

    name = StringField('Name', validators=[DataRequired(), Length(max=80)])
    slack_channel = StringField('Slack Channel', validators=[DataRequired(), Length(max=80)])
    submit = SubmitField('Create Area')


class AreaEditForm(FlaskForm):
    """Form for editing an existing area."""

    name = StringField('Name', validators=[DataRequired(), Length(max=80)])
    slack_channel = StringField('Slack Channel', validators=[DataRequired(), Length(max=80)])
    submit = SubmitField('Save Changes')
