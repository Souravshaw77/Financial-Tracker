const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const bcrypt = require('bcrypt');
const session = require('express-session');
const bodyParser = require('body-parser');
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(express.static('public'));
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.use(session({
    secret: 'your-secret-key',
    resave: false,
    saveUninitialized: true,
    cookie: { secure: false }
}));

// Database setup
const dbPath = path.join(__dirname, 'finance.db');
const db = new sqlite3.Database(dbPath);

// Initialize database tables
db.serialize(() => {
    // Users table
    db.run(`CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )`);

    // Expenses table
    db.run(`CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        category TEXT NOT NULL,
        description TEXT,
        date DATE NOT NULL,
        type TEXT DEFAULT 'expense',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )`);

    // Budget table
    db.run(`CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )`);
});

// Authentication middleware
function requireAuth(req, res, next) {
    if (req.session.userId) {
        next();
    } else {
        res.redirect('/login');
    }
}

// Routes
app.get('/', (req, res) => {
    if (req.session.userId) {
        res.redirect('/dashboard');
    } else {
        res.redirect('/login');
    }
});

app.get('/login', (req, res) => {
    res.render('login', { error: null });
});

app.post('/login', (req, res) => {
    const { username, password } = req.body;
    
    db.get('SELECT * FROM users WHERE username = ?', [username], (err, user) => {
        if (err) {
            return res.render('login', { error: 'Database error' });
        }
        
        if (!user) {
            return res.render('login', { error: 'Invalid username or password' });
        }
        
        bcrypt.compare(password, user.password, (err, result) => {
            if (err || !result) {
                return res.render('login', { error: 'Invalid username or password' });
            }
            
            req.session.userId = user.id;
            req.session.username = user.username;
            res.redirect('/dashboard');
        });
    });
});

app.get('/register', (req, res) => {
    res.render('register', { error: null });
});

app.post('/register', (req, res) => {
    const { username, email, password } = req.body;
    
    bcrypt.hash(password, 10, (err, hashedPassword) => {
        if (err) {
            return res.render('register', { error: 'Error creating account' });
        }
        
        db.run('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', 
               [username, email, hashedPassword], function(err) {
            if (err) {
                return res.render('register', { error: 'Username or email already exists' });
            }
            
            req.session.userId = this.lastID;
            req.session.username = username;
            res.redirect('/dashboard');
        });
    });
});

app.get('/dashboard', requireAuth, (req, res) => {
    const userId = req.session.userId;
    
    // Get recent expenses
    db.all(`SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC LIMIT 10`, 
           [userId], (err, expenses) => {
        if (err) {
            return res.render('dashboard', { 
                username: req.session.username, 
                expenses: [], 
                totalExpenses: 0,
                error: 'Error loading expenses' 
            });
        }
        
        // Calculate total expenses for current month
        const currentMonth = new Date().getMonth() + 1;
        const currentYear = new Date().getFullYear();
        
        db.get(`SELECT SUM(amount) as total FROM expenses 
                WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?`,
               [userId, currentMonth.toString().padStart(2, '0'), currentYear.toString()], 
               (err, result) => {
            const totalExpenses = result ? result.total || 0 : 0;
            
            res.render('dashboard', {
                username: req.session.username,
                expenses: expenses || [],
                totalExpenses: totalExpenses,
                error: null
            });
        });
    });
});

app.get('/add-expense', requireAuth, (req, res) => {
    res.render('add_expense', { error: null });
});

app.post('/add-expense', requireAuth, (req, res) => {
    const { amount, category, description, date, type } = req.body;
    const userId = req.session.userId;
    
    db.run('INSERT INTO expenses (user_id, amount, category, description, date, type) VALUES (?, ?, ?, ?, ?, ?)',
           [userId, amount, category, description, date, type || 'expense'], (err) => {
        if (err) {
            return res.render('add_expense', { error: 'Error adding expense' });
        }
        res.redirect('/dashboard');
    });
});

app.get('/budget', requireAuth, (req, res) => {
    const userId = req.session.userId;
    const currentMonth = new Date().getMonth() + 1;
    const currentYear = new Date().getFullYear();
    
    db.all('SELECT * FROM budget WHERE user_id = ? AND month = ? AND year = ?',
           [userId, currentMonth, currentYear], (err, budgets) => {
        res.render('budget', { 
            budgets: budgets || [], 
            error: null,
            currentMonth: currentMonth,
            currentYear: currentYear
        });
    });
});

app.post('/budget', requireAuth, (req, res) => {
    const { category, amount } = req.body;
    const userId = req.session.userId;
    const currentMonth = new Date().getMonth() + 1;
    const currentYear = new Date().getFullYear();
    
    db.run('INSERT INTO budget (user_id, category, amount, month, year) VALUES (?, ?, ?, ?, ?)',
           [userId, category, amount, currentMonth, currentYear], (err) => {
        if (err) {
            return res.render('budget', { 
                budgets: [], 
                error: 'Error setting budget',
                currentMonth: currentMonth,
                currentYear: currentYear
            });
        }
        res.redirect('/budget');
    });
});

app.get('/logout', (req, res) => {
    req.session.destroy();
    res.redirect('/login');
});

// Start server
app.listen(PORT, () => {
    console.log(`Finance Tracker running on port ${PORT}`);
});