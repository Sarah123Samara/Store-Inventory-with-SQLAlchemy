# Import necessary modules and classes
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime
import csv
import os

# Database setup
Base = declarative_base()


# Define the Product class for the database table
class Product(Base):
    __tablename__ = "products"
    product_id = Column(Integer, primary_key=True, autoincrement=True)
    product_name = Column(String)
    product_category = Column(String)
    product_quantity = Column(Integer)
    product_price = Column(Integer)  # Store price as cents (integer)
    date_updated = Column(DateTime, default=datetime.datetime.utcnow)


# Create the engine and bind it to the Base class
engine = create_engine("sqlite:///inventory.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


# Function to print the menu
def print_menu():
    menu_options = """
    \nINVENTORY MANAGEMENT

    \r1) Add product
    \r2) View all products
    \r3) Search for product
    \r4) Product analysis
    \r5) Delete product
    \r6) Make a backup of entire inventory 
    \r7) Exit
    """
    print(menu_options)
    return [str(i) for i in range(1, 8)]


# Function to make a backup of entire inventory
def make_backup():
    # Check if the backup file already exists
    if check_backup_existence():
        print("Backup has already been created.")
        return

    products = session.query(Product).all()

    with open("backup.csv", mode="w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(
            [
                "Product ID",
                "Product Name",
                "Product Category",
                "Product Quantity",
                "Product Price",
                "Date Updated",
            ]
        )
        for product in products:
            writer.writerow(
                [
                    product.product_id,
                    product.product_name,
                    product.product_category,
                    product.product_quantity,
                    product.product_price,
                    product.date_updated,
                ]
            )
    print("Backup of entire inventory created successfully in backup.csv")


# Function to check if backup file already exists
def check_backup_existence():
    return os.path.exists("backup.csv")


# Function to handle the menu
def menu():
    while True:
        options = print_menu()

        try:
            print()
            choice = input("What would you like to do? ").strip()
            print()
            if choice in options:
                return choice
            else:
                print(
                    """
                \rPlease enter a valid option from the above.
                \rA number from 1-7.
                """
                )
        except ValueError:
            print(
                """
            \rPlease enter a valid number from 1-7.
            """
            )


# Function to add a product
def add_product():
    while True:
        product_name = input(
            "Enter the product name (press Enter to go back to the menu): "
        ).strip()
        if not product_name:
            print("Returning to the menu.")
            return

        product_category = input("Enter the product category: ").strip()

        # Handling date input with proper error message
        while True:
            date_str = input("Enter the entry date (e.g., January 1, 2022): ").strip()
            date = clean_date(date_str)
            if date is not None:
                break
            else:
                print("Invalid date format. Please try again.")

        # Handling price input with proper error message
        while True:
            try:
                price_str = input("Enter the price (e.g., 3.19): ").strip()
                price = clean_price(price_str)
                if price is not None:
                    # Convert dollars to cents (integer)
                    price = int(price * 100)
                    break
                else:
                    print("Invalid price format. Please try again.")
            except ValueError:
                print("Invalid price format. Please enter a valid number.")

        # Handling quantity input with proper error message
        while True:
            try:
                product_quantity = int(input("Enter the product quantity: ").strip())
                if product_quantity >= 0:
                    break
                else:
                    print("Quantity must be a non-negative integer. Please try again.")
            except ValueError:
                print("Invalid quantity format. Please enter a valid number.")

        print("\nPlease review the information:")
        print(f"\nName: {product_name}")
        print(f"\nCategory: {product_category}")
        print(f"\nEntry Date: {date.strftime('%B %d, %Y')}")
        print(f"\nPrice: ${price / 100:.2f}")  # Display price in dollars
        print(f"\nQuantity: {product_quantity}")

        while True:
            print()
            confirmation = (
                input(
                    "Are you sure you have filled in the information correctly? (Yes/No) (press Enter to go back to the menu): "
                )
                .strip()
                .lower()
            )

            if confirmation == "":  # If the user pressed Enter
                print("Returning to the menu.")
                return

            if confirmation == "yes":
                # Check if a product with the same information already exists
                existing_product = (
                    session.query(Product)
                    .filter_by(
                        product_name=product_name,
                        product_category=product_category,
                        product_quantity=product_quantity,
                        product_price=price,
                    )
                    .first()
                )

                if existing_product:
                    print("Product is already in the inventory.")
                    return

                # Create a new product with the provided information
                new_product = Product(
                    product_name=product_name,
                    product_category=product_category,
                    product_quantity=product_quantity,
                    product_price=price,
                    date_updated=datetime.datetime.utcnow(),
                )
                session.add(new_product)
                session.commit()
                print("Product added successfully!")

                # Create or append to the backup.csv file
                with open("backup.csv", mode="a", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    if csvfile.tell() == 0:
                        # Write the header row if the file is empty
                        writer.writerow(
                            [
                                "Product ID",
                                "Product Name",
                                "Product Category",
                                "Product Quantity",
                                "Product Price",
                                "Date Updated",
                            ]
                        )
                    writer.writerow(
                        [
                            new_product.product_id,
                            new_product.product_name,
                            new_product.product_category,
                            new_product.product_quantity,
                            new_product.product_price,
                            new_product.date_updated,
                        ]
                    )

                return
            elif confirmation == "no":
                print("Please fill in the information again.\n")
                break
            else:
                print("Invalid input. Please enter either 'Yes' or 'No'.\n")


def view_all_products():
    products = session.query(Product).all()

    if not products:
        print("No products found.")
        return

    for product in products:
        print(
            f"ID: {product.product_id}  Name: {product.product_name}  Category: {product.product_category}  Quantity: {product.product_quantity}  Price: ${product.product_price / 100:.2f}  Date Updated: {product.date_updated}"
        )


# Function to clean date input
def clean_date(date_str):
    try:
        # Attempt to parse the date with multiple formats
        date_formats = ["%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"]
        for format_str in date_formats:
            try:
                return datetime.datetime.strptime(date_str, format_str).date()
            except ValueError:
                pass  # Continue to the next format if the current one fails

        # If none of the formats match, return None
        return None
    except ValueError:
        return None


# Function to clean price input
def clean_price(price_str):
    try:
        return float(price_str)
    except ValueError:
        return None


# Function to delete products
def delete_product():
    name_to_delete = input(
        "Enter the name of the product you want to delete (press Enter to go back to the menu): "
    )

    if not name_to_delete:
        print("\nDeletion canceled.")
        return

    products = (
        session.query(Product)
        .filter(Product.product_name.ilike(f"%{name_to_delete}%"))
        .all()
    )

    if products:
        print("Products found with matching name:")
        for i, product in enumerate(products, 1):
            print(
                f"{i}) ID: {product.product_id}  Name: {product.product_name}  Category: {product.product_category}  Quantity: {product.product_quantity}  Price: ${product.product_price / 100:.2f}  Date Updated: {product.date_updated}"
            )

        while True:
            try:
                print()
                print(
                    "Enter the number(s) of the product(s) you want to delete (comma-separated) press Enter to cancel: "
                )
                choice_input = input().strip()

                if not choice_input:
                    print("\nDeletion canceled.")
                    return

                choices = [int(choice) for choice in choice_input.split(",")]

                invalid_choices = [c for c in choices if c < 0 or c > len(products)]

                if invalid_choices:
                    print(
                        f"{len(invalid_choices)} of the numbers you have entered is/are invalid. Please enter numbers that are valid."
                    )
                    continue

                for choice in choices:
                    product_to_delete = products[choice - 1]
                    session.delete(product_to_delete)
                    print(
                        f"Product '{product_to_delete.product_name}' deleted successfully!"
                    )

                session.commit()
                break
            except ValueError:
                print("Invalid input. Please enter valid numbers.")
    else:
        print(f"No matching products with name '{name_to_delete}' found.")


# Function to search for a product
def search_for_product():
    name_to_search = input(
        "Enter the product name to search (press enter to go back to menu): "
    )

    if not name_to_search:
        return  # If the user presses enter, return to the menu

    products = (
        session.query(Product)
        .filter(Product.product_name.ilike(f"%{name_to_search}%"))
        .all()
    )

    if products:
        print("Products found with matching name:")
        for product in products:
            print(
                f"ID: {product.product_id}  Name: {product.product_name}  Category: {product.product_category}  Quantity: {product.product_quantity}  Price: ${product.product_price / 100:.2f}  Date Updated: {product.date_updated}"
            )
    else:
        print(f"No matching products with name '{name_to_search}' found.")


# Function to analyze products
def products_analysis():
    print("\nDATA ANALYSIS\n")

    # Priciest product
    priciest_product = (
        session.query(Product).order_by(Product.product_price.desc()).first()
    )
    if priciest_product:
        print(
            f"Priciest Product: {priciest_product.product_name} - ${priciest_product.product_price / 100:.2f}"
        )
    else:
        print("No products available for analysis.")

    # Cheapest product
    cheapest_product = session.query(Product).order_by(Product.product_price).first()
    if cheapest_product:
        print(
            f"Cheapest Product: {cheapest_product.product_name} - ${cheapest_product.product_price / 100:.2f}"
        )
    else:
        print("No products available for analysis.")

    # Number of products available
    num_products = session.query(Product).count()
    print(f"Number of Products Available: {num_products}")

    # Newest product
    newest_product = (
        session.query(Product).order_by(Product.date_updated.desc()).first()
    )
    if newest_product:
        print(
            f"Newest Product: {newest_product.product_name} - {newest_product.date_updated}"
        )
    else:
        print("No products available for analysis.")

    # Oldest product
    oldest_product = session.query(Product).order_by(Product.date_updated).first()
    if oldest_product:
        print(
            f"Oldest Product: {oldest_product.product_name} - {oldest_product.date_updated}"
        )
    else:
        print("No products available for analysis.")


# Function to run the app
def app():
    app_running = True
    while app_running:
        menu_choice = menu()

        if menu_choice == "1":
            add_product()
        elif menu_choice == "2":
            view_all_products()
        elif menu_choice == "3":
            search_for_product()
        elif menu_choice == "4":
            products_analysis()
        elif menu_choice == "5":
            delete_product()
        elif menu_choice == "6":
            make_backup()
        elif menu_choice == "7":
            print("Have a nice day!")
            print()
            app_running = False
        else:
            print("Invalid option. Please try again.")


# Entry point of the program
if __name__ == "__main__":
    app()
