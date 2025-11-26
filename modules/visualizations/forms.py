# forms.py
from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, StringField
from wtforms.validators import DataRequired


class VisualizationForm(FlaskForm):
    report_type = SelectField('Report Type', choices=[
        ('sales', 'Sales Report'),
        ('inventory', 'Inventory Report'),
        ('expenses', 'Expenses Report')
    ], validators=[DataRequired()])

    chart_type = SelectField('Chart Type', choices=[
        ('bar', 'Bar Chart'),
        ('line', 'Line Chart'),
        ('pie', 'Pie Chart')
    ], validators=[DataRequired()])

    start_date = DateField('Start Date', format='%Y-%m-%d')
    end_date = DateField('End Date', format='%Y-%m-%d')

    x_axis = SelectField('X-Axis Field', choices=[])
    y_axis = SelectField('Y-Axis Field', choices=[])
    labels = SelectField('Labels Field', choices=[])
    values = SelectField('Values Field', choices=[])
    title = StringField('Chart Title')