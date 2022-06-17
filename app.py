from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta

import random
from faker import Faker

# Allows us to generate fake data
fake = Faker()


# Instantiating Flask object.
app = Flask(__name__) 
# Setting Connection String
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# To suppress warnings in the terminal
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# To instantiate the SQL Alchemy object
db = SQLAlchemy(app)

# Class in Flask SQLAlchemy translates to a table in the database.
# This project concerns an E-Commerce site.
class Customer(db.Model):
    # The usage of id in Flask SQLAlchemy is crucial to keep a track of what's happening.
    id = db.Column(db.Integer, primary_key= True)
    # Nullable enforces the requirement of values
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    # Address can well spill over 50 characters
    address = db.Column(db.String(500), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    postcode = db.Column(db.String(50), nullable=False)
    # One customer should possess one unique email
    email = db.Column(db.String(50), nullable=False, unique= True)

    # Creates  a relationship between the two tables.
    # Backref creates a pseudo-column between the two tables that allows us to do things like: 
    # order.customer -> gets the customer who made the order or customer.orders -> gets all the orders made by a customer
    orders = db.relationship('Order', backref= 'customer')

# The order and product tables entail a many-to-many relationship (An order can contain many products, a single product can appear in multiple orders).
# Therefore, below is the creation of an association table between the two.

order_product = db.Table('order_product', 
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key= True),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key= True)
)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    # The order date will be set to the time the order object was instantiated incase a date wasn't provided.
    order_date = db.Column(db.DateTime, nullable= False, default= datetime.utcnow)
    # The next too can be NULL incase an order wasn't shipped or delivered yet.
    ship_date = db.Column(db.DateTime)
    delivered_date = db.Column(db.DateTime)
    coupon_code = db.Column(db.String(50))
    # Foreign key to the Customer Table, each order will have some customer associated with it.
    # The table specified in db.ForeignKey('') should be in lower-case followed by a period and the attribute.
    # Every order has to have a customer -> nullable = False
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable= False)

    # To access the products of a certain order, the relationship has to go through the association table.
    products = db.relationship('Product', secondary= order_product)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key= True)
    name = db.Column(db.String(50), nullable= False, unique= True)
    price = db.Column(db.Integer, nullable= False)

# Function to create fake customer data for testing purpose.
def add_customers():
    for _ in range(100):
        customer = Customer(
            first_name=fake.first_name(),
            last_name= fake.last_name(),
            address = fake.address(),
            city=fake.city(),
            postcode=fake.postcode(),
            email=fake.email()
        )

        db.session.add(customer)
    db.session.commit()

def add_orders():
    # Get all customers to generate order.
    customers = Customer.query.all()

    for _ in range(1000):
        # Select a random customer.
        customer = random.choice(customers)

        # Set a fake ordered date.
        ordered_date = fake.date_time_this_year()

        # Select shipped date after the ordered date 90% of the time with the 10% of the time it being set to None.
        shipped_date = random.choices([None, fake.date_time_between(start_date= ordered_date)], [10, 90])[0]

        delivered_date = None
        
        # If a shipping date exists, select a date after the shipping 50% of the time with the rest of the time it being None.
        if shipped_date:
            delivered_date = random.choices([None, fake.date_time_between(start_date= shipped_date)], [50, 50])[0]

        # Select the coupon code to be None 85% of the time with the rest 15% of the time it being set to the other options in the list.
        coupon_code = random.choices([None, '50OFF', 'FREESHIPPING', 'BUYONEGETONE'], [85, 5, 5, 5])[0]

        order = Order(
            order_date= ordered_date,
            ship_date = shipped_date,
            delivered_date= delivered_date,
            coupon_code= coupon_code,
            customer_id= customer.id
        )

        db.session.add(order)
    db.session.commit()

def add_products():
    for _ in range(10):
        product= Product(
            name= fake.color_name(),
            price=random.randint(10, 100)
        )
        db.session.add(product)
    db.session.commit()

def add_order_products():
    orders = Order.query.all()
    products = Product.query.all()

    for order in orders:
        # Generate the number of products to be selected from the product list.
        k = random.randint(1, 3)

        # Select 'k' products from the products list.
        purchased_products = random.sample(products, k)

        # Extend the products list of a particular order to include the selected products.
        order.products.extend(purchased_products)

    db.session.commit()

def create_random_data():
    db.create_all()
    add_customers()
    add_orders()
    add_products()
    add_order_products()

def get_orders_by(customer_id):
    '''This function returns the order history of a particular customer denoted by their customer ID.'''
    orders = Order.query.filter_by(customer_id= customer_id).all()

    customer = Customer.query.filter_by(id= customer_id).first()

    print("Order history of", customer.first_name, customer.last_name)

    for order in orders:
        print(order.order_date)

def get_pending_orders():
    '''This function will return all the pending orders in the store with the most recent one at the top.'''
    pending_orders = Order.query.filter(Order.ship_date.is_(None)).order_by(Order.order_date.desc()).all()
    print('Pending Orders:')

    for order in pending_orders:
        print(order.order_date)

def how_many_customers():
    '''This function returns the count of all the customers.'''
    print("The number of recorded customers is", 
        Customer.query.count())

def orders_with_code():
    '''This functions return the codes of all those orders that contain a coupon code other than FREESHIPPING'''
    orders = Order.query.filter(Order.coupon_code.is_not(None)).filter(Order.coupon_code != 'FREESHIPPING').all()

    print('Orders with Coupon Code:')
    for order in orders:
        print(order.coupon_code)

def revenue_in_last_x_days(x_days= 30):
    '''This function returns the revenue generated in the last x days specified in the arguments.'''
    print("Revenue for the last {0} days: ".format(x_days))

    print(db.session.query(
        db.func.sum(Product.price)
    ).join(order_product).join(Order).filter(
        Order.order_date > datetime.now() - timedelta(days= x_days)
    ).scalar())

def average_fulfillment_time():
    '''This function returns the average fulfillment time on the orders.'''

    print('The average fulfillment time of an order is: {}'.format(
        db.session.query(
            db.func.time(
                db.func.avg(
                    db.func.strftime('%s', Order.ship_date) - db.func.strftime('%s', Order.order_date)
                ),
                'unixepoch'
            )
        ).filter(Order.ship_date.is_not(None)).scalar()
    ))

def get_customers_who_spent_more_than_x_dollars(amount= 500):
    '''This function returns the names of the customers who've spent more than a certain specified amount of dollars.'''

    print("Customers who have spent more than {} dollars:".format(amount))

    customers = db.session.query(Customer).join(Order).join(order_product).join(Product).group_by(Customer).having(
        db.func.sum(Product.price) > amount)

    for customer in customers:
        print(customer.first_name, customer.last_name)

