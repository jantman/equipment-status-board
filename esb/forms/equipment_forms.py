"""Equipment forms for area and equipment management."""

from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    DecimalField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Length, Optional


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


class EquipmentCreateForm(FlaskForm):
    """Form for creating a new equipment record."""

    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    manufacturer = StringField('Manufacturer', validators=[DataRequired(), Length(max=200)])
    model = StringField('Model', validators=[DataRequired(), Length(max=200)])
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Length(max=200)])
    acquisition_date = DateField('Acquisition Date', validators=[Optional()])
    acquisition_source = StringField('Acquisition Source', validators=[Length(max=200)])
    acquisition_cost = DecimalField('Acquisition Cost', places=2, validators=[Optional()])
    warranty_expiration = DateField('Warranty Expiration', validators=[Optional()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Equipment')


class EquipmentEditForm(FlaskForm):
    """Form for editing an existing equipment record."""

    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    manufacturer = StringField('Manufacturer', validators=[DataRequired(), Length(max=200)])
    model = StringField('Model', validators=[DataRequired(), Length(max=200)])
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Length(max=200)])
    acquisition_date = DateField('Acquisition Date', validators=[Optional()])
    acquisition_source = StringField('Acquisition Source', validators=[Length(max=200)])
    acquisition_cost = DecimalField('Acquisition Cost', places=2, validators=[Optional()])
    warranty_expiration = DateField('Warranty Expiration', validators=[Optional()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Changes')
