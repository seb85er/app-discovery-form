from flask import Flask, render_template, redirect, url_for, request  # Added 'request' to imports
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, FieldList, FormField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Enable CSRF protection
csrf = CSRFProtect(app)

# Form for entering server information
class ServerForm(FlaskForm):
    server_name = StringField('Server Name', validators=[DataRequired()])

# Main App Discovery Form
class AppDiscoveryForm(FlaskForm):
    app_name = StringField('App Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    servers = FieldList(FormField(ServerForm), min_entries=1, max_entries=10)
    submit = SubmitField('Submit')

# Default landing page
@app.route('/')
def home():
    return render_template('home.html')

# Route for the form to add an application
@app.route('/add-application', methods=['GET', 'POST'])
def add_application():
    form = AppDiscoveryForm()

    if request.method == 'POST':  # Fixing the 'request' usage by ensuring it's imported
        # If "add_server" was clicked, add a new server field
        if 'add_server' in request.form:
            form.servers.append_entry()
            return render_template('add_application.html', form=form)

        # If the Submit button was clicked, validate the form
        if form.validate_on_submit():
            app_name = form.app_name.data
            description = form.description.data
            servers = [server.server_name.data for server in form.servers]
            return render_template('success.html', app_name=app_name, description=description, servers=servers)
        else:
            print("Form validation failed")
            print(form.errors)  # Print form validation errors

    return render_template('add_application.html', form=form)

if __name__ == '__main__':
    app.run(debug=True)
