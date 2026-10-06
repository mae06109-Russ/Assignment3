from flask import Flask, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
import os
import MySQLdb.cursors
from flask_bootstrap import Bootstrap5


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234' 
app.config['MYSQL_DB'] = 'GiveRelay' 

mysql = MySQL(app)
app.config['UPLOAD_FOLDER'] = 'static/img'

@app.route('/test')
def test_page():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) 
    cursor.execute("SELECT * FROM Project ORDER BY projectId DESC") 
    campaigns = cursor.fetchall()
    cursor.close()

    return render_template('test.html', campaigns=campaigns)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ...
        pass
    return render_template('login.html')

@app.route('/')
def home():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor) 
    cursor.execute("SELECT * FROM Project ORDER BY projectId DESC") 
    campaigns = cursor.fetchall()
    cursor.close()

    return render_template('index.html', campaigns=campaigns)



@app.route('/campaign/<int:project_id>')
def campaign_detail(project_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    cursor.execute("SELECT * FROM Project WHERE projectId = %s", (project_id,))
    campaign = cursor.fetchone()
    
    cursor.execute("SELECT SUM(amount) as total_raised FROM Donation WHERE projectId = %s", (project_id,))
    stats = cursor.fetchone()
    raised = stats['total_raised'] if stats['total_raised'] else 0
    
    goal = campaign['goalAmount']
    progress = int((raised / goal) * 100) if goal > 0 else 0
    
    cursor.close()

    return render_template('campaign2.html', campaign=campaign, raised=raised, progress=progress)

@app.route('/donation/<int:project_id>', methods=['GET', 'POST'])
def donation_page(project_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        amount = request.form['money']
        supporter_name = request.form['Name']
        is_anonymous = 1 if request.form.get('anonymousCheck') == 'on' else 0
        email = request.form['email']
        payment_method = request.form['method']
        message = request.form['message']
        
        cursor.execute("""
            INSERT INTO Donation 
            (projectId, amount, supporterName, isAnonymous, email, paymentMethod, message)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (project_id, amount, supporter_name, is_anonymous, email, payment_method, message))
        
        mysql.connection.commit()
        return redirect(url_for('donation_page', project_id=project_id))

    
    cursor.execute("SELECT * FROM Project WHERE projectId = %s", (project_id,))
    campaign = cursor.fetchone()
    
    cursor.execute("SELECT SUM(amount) as total_raised FROM Donation WHERE projectId = %s", (project_id,))
    stats = cursor.fetchone()
    raised = stats['total_raised'] if stats['total_raised'] else 0
    
    goal = campaign['goalAmount']
    progress = int((raised / goal) * 100) if goal > 0 else 0
    
    cursor.execute("""
        SELECT supporterName, isAnonymous, amount, message 
        FROM Donation 
        WHERE projectId = %s 
        ORDER BY amount DESC 
        LIMIT 7
    """, (project_id,))
    leaderboard = cursor.fetchall()
    
    cursor.close()
    
    return render_template('donation2.html', campaign=campaign, raised=raised, progress=progress, leaderboard=leaderboard)


@app.route('/create-campaign', methods=['GET', 'POST'])
def create_campaign():
    if request.method == 'POST':
        
        title = request.form.get('title')
        category_id = request.form.get('categoryId')
        goal_amount = request.form.get('goalAmount')
        start_date = request.form.get('startDate')
        end_date = request.form.get('endDate')
        location = request.form.get('location')
        beneficiary = request.form.get('beneficiary')
        description = request.form.get('description')
        
        
        file = request.files.get('image') 
        filename = 'default.png'
        if file and file.filename != '':
            filename = file.filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        status = 'Active'
        creator_id = 1 
        
        
        cursor = mysql.connection.cursor()
        insert_query = """
            INSERT INTO Project 
            (creatorId, categoryId, title, description, goalAmount, status, startDate, endDate, image, location, beneficiary) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_query, (
            creator_id, category_id, title, description, goal_amount, status, start_date, end_date, filename, location, beneficiary
        ))
        
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('create_campaign')) 

    return render_template('create_campaign.html')

if __name__ == '__main__':
    app.run(debug=True)