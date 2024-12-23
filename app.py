from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import os
from datetime import datetime
from flask import send_from_directory

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ------------------MySQL connection--------------------------------

db_config = {
    "host": "localhost",
    "user": "root",
    "database": "student_management"
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# ------------------------Register student-----------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username') 
        password = request.form.get('password')

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()

            # Check if username exists
            cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                flash('Username already exists. Please choose another one.', 'danger')
                return redirect(url_for('register'))

            # Insert new user
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'danger')
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    return render_template('register.html')


# ------------------------Login student---------------------------------
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')  
        password = request.form.get('password')

        connection = None
        cursor = None

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
            user = cursor.fetchone()

            if user:
                session['user'] = user[0]  # Store user ID in session
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials, please try again.', 'danger')
                return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
            return redirect(url_for('login'))
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()
    return render_template('login.html')

# -----------------------------Dashboard----------------------------------

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# -----------------------------backup student------------------------------

@app.route('/backupStudent', methods=['GET'])
def backup_student():
    backup_file = "student_backup.txt"
    try:
        # Fetch student data from the database
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM students")
        records = cursor.fetchall()

        # Write data to a text file
        with open(backup_file, "w") as file:
            for record in records:
                file.write(", ".join(map(str, record)) + "\n")

        flash(f"Backup completed! File saved as {backup_file}.", 'success')
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
    except Exception as e:
        flash(f"Error during backup: {e}", 'danger')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    # Provide a link to download the backup file
    return render_template('backupStudent.html', file_name=backup_file)

@app.route('/download/<path:filename>')
def download_file(filename):
    backup_dir = os.getcwd()  
    return send_from_directory(backup_dir, filename, as_attachment=True)


# --------------------------add student--------------------------------

@app.route('/addStudent', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        email = request.form.get('email')

        try:
            # Insert data into the database
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO students (first_name, last_name, date_of_birth, gender, email)
                VALUES (%s, %s, %s, %s, %s)
            """, (first_name, last_name, dob, gender, email))
            connection.commit()
            flash('Student added successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'danger')
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for('dashboard'))
    return render_template('addStudent.html')


# --------------------------------view student--------------------------

@app.route('/viewStudent', methods=['GET'])
def view_student():
    try:
        # Fetch data from the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)  # Use dictionary=True to get column names
        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
        students = []
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    # Render the template with student data
    return render_template('viewStudent.html', students=students)


# ----------------------------update student----------------------------

@app.route('/updateStudent/<int:student_id>', methods=['GET', 'POST'])
def update_student(student_id):
    if request.method == 'POST':
        # Get updated data from the form
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        dob = request.form.get('dob')
        gender = request.form.get('gender')
        email = request.form.get('email')

        try:
            connection = get_db_connection()
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE students
                SET first_name = %s, last_name = %s, date_of_birth = %s, gender = %s, email = %s
                WHERE student_id = %s
            """, (first_name, last_name, dob, gender, email, student_id))
            connection.commit()
            flash('Student updated successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Database error: {err}", 'danger')
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

        return redirect(url_for('view_student'))

    # Fetch student data for the form
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger') 
        student = None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return render_template('updateStudent.html', student=student)

# --------------------------delete student-------------------------------

@app.route('/deleteStudent/<int:student_id>', methods=['POST', 'GET'])
def delete_student(student_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        connection.commit()
        flash('Student deleted successfully!', 'success')
    except mysql.connector.Error as err:
        flash(f"Database error: {err}", 'danger')
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

    return redirect(url_for('view_student'))

if __name__ == "__main__":
    app.run(debug=True, port=8080)

# --------------------------Close connection on exit-----------------------

connection = get_db_connection()
connection.close()