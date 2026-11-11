import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://127.0.0.1:27017')
DB_NAME = os.environ.get('DB_NAME', 'hostel_db')

def seed():
    print("=" * 60)
    print("  HOSTEL MANAGEMENT SYSTEM - DATABASE SEEDING")
    print("=" * 60)
    print(f"Connecting to MongoDB at: {MONGO_URI} (DB: {DB_NAME})")

    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[DB_NAME]
    except Exception as e:
        print(f"\n[ERROR] Could not connect to MongoDB: {e}")
        print("Please make sure MongoDB is running locally or check MONGO_URI in .env.")
        return

    # Drop existing collections for clean seed
    collections = [
        'users', 'students', 'blocks', 'rooms', 'allocations',
        'fees', 'payments', 'mess_menu', 'meal_attendance',
        'complaints', 'leaves', 'visitors', 'notices'
    ]
    for coll in collections:
        db[coll].drop()
    print("Cleaned up existing collections.")

    # 1. Users (Admin and Warden)
    print("\n1. Creating Admin & Warden accounts...")
    admin_id = str(db.users.insert_one({
        'username': 'admin',
        'password': generate_password_hash('admin123'),
        'role': 'admin',
        'name': 'Chief Administrator',
        'email': 'admin@hostel.edu',
        'created_at': datetime.now()
    }).inserted_id)

    warden_id = str(db.users.insert_one({
        'username': 'warden',
        'password': generate_password_hash('warden123'),
        'role': 'warden',
        'name': 'Prof. Rajesh Sharma',
        'email': 'warden@hostel.edu',
        'created_at': datetime.now()
    }).inserted_id)

    # 2. Blocks
    print("2. Creating Blocks...")
    block_a_id = str(db.blocks.insert_one({
        'name': 'Block A - Boys Hostel',
        'floors': 3,
        'description': 'Main boys residential wing, 3 floors with recreation hall',
        'created_at': datetime.now()
    }).inserted_id)

    block_b_id = str(db.blocks.insert_one({
        'name': 'Block B - Girls Hostel',
        'floors': 3,
        'description': 'Main girls residential wing, 3 floors with study lounge',
        'created_at': datetime.now()
    }).inserted_id)

    # 3. Rooms (10 rooms)
    print("3. Creating 10 Rooms...")
    room_definitions = [
        # Block A (5 rooms)
        {'block_id': block_a_id, 'room_number': 'A-101', 'floor': 1, 'room_type': 'Single', 'capacity': 1, 'status': 'Available', 'amenities': 'AC, Study Table, Balcony'},
        {'block_id': block_a_id, 'room_number': 'A-102', 'floor': 1, 'room_type': 'Double', 'capacity': 2, 'status': 'Available', 'amenities': 'Fan, Study Tables, Wardrobes'},
        {'block_id': block_a_id, 'room_number': 'A-201', 'floor': 2, 'room_type': 'Double', 'capacity': 2, 'status': 'Available', 'amenities': 'Fan, Study Tables, Attached Bath'},
        {'block_id': block_a_id, 'room_number': 'A-202', 'floor': 2, 'room_type': 'Triple', 'capacity': 3, 'status': 'Available', 'amenities': 'Fan, 3 Cots, 3 Desks'},
        {'block_id': block_a_id, 'room_number': 'A-301', 'floor': 3, 'room_type': 'Single', 'capacity': 1, 'status': 'Maintenance', 'amenities': 'Under renovation'},
        # Block B (5 rooms)
        {'block_id': block_b_id, 'room_number': 'B-101', 'floor': 1, 'room_type': 'Single', 'capacity': 1, 'status': 'Available', 'amenities': 'AC, Attached Bath, Balcony'},
        {'block_id': block_b_id, 'room_number': 'B-102', 'floor': 1, 'room_type': 'Double', 'capacity': 2, 'status': 'Available', 'amenities': 'Fan, 2 Study Desks'},
        {'block_id': block_b_id, 'room_number': 'B-201', 'floor': 2, 'room_type': 'Double', 'capacity': 2, 'status': 'Available', 'amenities': 'Fan, Wardrobe, Large Window'},
        {'block_id': block_b_id, 'room_number': 'B-202', 'floor': 2, 'room_type': 'Triple', 'capacity': 3, 'status': 'Available', 'amenities': 'Fan, 3 Beds, Study Area'},
        {'block_id': block_b_id, 'room_number': 'B-301', 'floor': 3, 'room_type': 'Single', 'capacity': 1, 'status': 'Available', 'amenities': 'Fan, Balcony View'}
    ]

    room_ids = []
    for r in room_definitions:
        r['created_at'] = datetime.now()
        r_id = str(db.rooms.insert_one(r).inserted_id)
        room_ids.append((r['room_number'], r_id, r['capacity']))

    # 4. Students (15 students with user accounts)
    print("4. Creating 15 Students...")
    raw_students = [
        ("Aarav Sharma", "2024CS01", "B.Tech CSE", "1st", "9876543210", "aarav@student.edu", "Ramesh Sharma", "9876543290", "12 Civil Lines, Jaipur"),
        ("Ananya Iyer", "2024CS02", "B.Tech CSE", "1st", "9876543211", "ananya@student.edu", "Suresh Iyer", "9876543291", "45 Gandhi Road, Chennai"),
        ("Rohan Verma", "2024ME01", "B.Tech Mech", "2nd", "9876543212", "rohan@student.edu", "Alok Verma", "9876543292", "88 Park Street, Kolkata"),
        ("Priya Nair", "2024EC01", "B.Tech ECE", "2nd", "9876543213", "priya@student.edu", "Venkat Nair", "9876543293", "23 MG Road, Kochi"),
        ("Kabir Mehta", "2024CS03", "B.Tech CSE", "3rd", "9876543214", "kabir@student.edu", "Sunil Mehta", "9876543294", "101 Marine Drive, Mumbai"),
        ("Diya Patel", "2024EE01", "B.Tech EEE", "3rd", "9876543215", "diya@student.edu", "Kishore Patel", "9876543295", "56 SG Highway, Ahmedabad"),
        ("Vikram Singh", "2024CE01", "B.Tech Civil", "4th", "9876543216", "vikram@student.edu", "Mahendra Singh", "9876543296", "77 Mall Road, Shimla"),
        ("Ishita Sen", "2024CS04", "B.Tech CSE", "1st", "9876543217", "ishita@student.edu", "Debashis Sen", "9876543297", "34 Salt Lake, Kolkata"),
        ("Aditya Rao", "2024ME02", "B.Tech Mech", "2nd", "9876543218", "aditya@student.edu", "Prabhakar Rao", "9876543298", "90 Banjara Hills, Hyderabad"),
        ("Sneha Kulkarni", "2024EC02", "B.Tech ECE", "3rd", "9876543219", "sneha@student.edu", "Milind Kulkarni", "9876543299", "14 FC Road, Pune"),
        ("Arjun Gupta", "2024CS05", "B.Tech CSE", "4th", "9876543220", "arjun@student.edu", "Rakesh Gupta", "9876543200", "62 Model Town, Delhi"),
        ("Meera Menon", "2024EE02", "B.Tech EEE", "1st", "9876543221", "meera@student.edu", "Gopinath Menon", "9876543201", "19 Palayam, Trivandrum"),
        ("Devansh Joshi", "2024CE02", "B.Tech Civil", "2nd", "9876543222", "devansh@student.edu", "Satish Joshi", "9876543202", "33 Rajpur Road, Dehradun"),
        ("Tanvi Deshmukh", "2024CS06", "B.Tech CSE", "3rd", "9876543223", "tanvi@student.edu", "Ashok Deshmukh", "9876543203", "81 Shivaji Nagar, Nagpur"),
        ("Yash Agarwal", "2024ME03", "B.Tech Mech", "4th", "9876543224", "yash@student.edu", "Deepak Agarwal", "9876543204", "49 Hazratganj, Lucknow")
    ]

    student_records = []
    for i, s in enumerate(raw_students, 1):
        username = f"student{i}"
        user_id = str(db.users.insert_one({
            'username': username,
            'password': generate_password_hash('student123'),
            'role': 'student',
            'name': s[0],
            'email': s[5],
            'created_at': datetime.now()
        }).inserted_id)

        stu_id = str(db.students.insert_one({
            'user_id': user_id,
            'name': s[0],
            'roll_number': s[1],
            'course': s[2],
            'year': s[3],
            'phone': s[4],
            'email': s[5],
            'guardian_name': s[6],
            'guardian_phone': s[7],
            'address': s[8],
            'photo': None,
            'status': 'Active',
            'created_at': datetime.now()
        }).inserted_id)
        student_records.append({'id': stu_id, 'name': s[0], 'roll': s[1], 'username': username})

    # 5. Room Allocations (allocate first 9 students)
    print("5. Allocating rooms...")
    allocations_plan = [
        (student_records[0]['id'], room_ids[0][1]),  # Aarav -> A-101 (Single, full)
        (student_records[1]['id'], room_ids[5][1]),  # Ananya -> B-101 (Single, full)
        (student_records[2]['id'], room_ids[1][1]),  # Rohan -> A-102 (Double, 1/2)
        (student_records[3]['id'], room_ids[6][1]),  # Priya -> B-102 (Double, 1/2)
        (student_records[4]['id'], room_ids[2][1]),  # Kabir -> A-201 (Double, 1/2)
        (student_records[5]['id'], room_ids[7][1]),  # Diya -> B-201 (Double, 1/2)
        (student_records[6]['id'], room_ids[3][1]),  # Vikram -> A-202 (Triple, 1/3)
        (student_records[7]['id'], room_ids[8][1]),  # Ishita -> B-202 (Triple, 1/3)
        (student_records[8]['id'], room_ids[3][1]),  # Aditya -> A-202 (Triple, 2/3)
    ]

    for sid, rid in allocations_plan:
        db.allocations.insert_one({
            'student_id': sid,
            'room_id': rid,
            'allocated_at': datetime.now() - timedelta(days=60),
            'status': 'Active',
            'notes': 'Academic year 2024-25 allocation'
        })

    # Mark A-101 and B-101 as Full
    db.rooms.update_one({'_id': client[DB_NAME].rooms.find_one({'room_number': 'A-101'})['_id']}, {'$set': {'status': 'Full'}})
    db.rooms.update_one({'_id': client[DB_NAME].rooms.find_one({'room_number': 'B-101'})['_id']}, {'$set': {'status': 'Full'}})

    # 6. Fees and Payments
    print("6. Creating Fees and Payments...")
    fee_structures = [
        ('Hostel Fee', 45000.0, '2024-12-15'),
        ('Mess Fee', 25000.0, '2024-11-30')
    ]

    for idx, stu in enumerate(student_records):
        # Every student gets Hostel Fee
        h_fee_id = str(db.fees.insert_one({
            'student_id': stu['id'],
            'fee_type': 'Hostel Fee',
            'amount': 45000.0,
            'paid_amount': 0.0,
            'due_date': '2024-12-15',
            'description': 'Semester 1 Accommodation Fee',
            'status': 'Pending',
            'created_at': datetime.now() - timedelta(days=45)
        }).inserted_id)

        # First 5 students paid full
        if idx < 5:
            db.payments.insert_one({
                'fee_id': h_fee_id,
                'student_id': stu['id'],
                'amount': 45000.0,
                'payment_date': (date.today() - timedelta(days=30 - idx * 5)).isoformat(),
                'mode': 'Online Transfer',
                'receipt_number': f'REC-2024-{1000 + idx}',
                'recorded_by': admin_id,
                'created_at': datetime.now() - timedelta(days=30 - idx * 5)
            })
            db.fees.update_one({'_id': client[DB_NAME].fees.find_one({'_id': client[DB_NAME].fees.find()[0]['_id'] if False else None}) or db.fees.find_one({'student_id': stu['id']})['_id']}, {'$set': {'paid_amount': 45000.0, 'status': 'Paid'}})

        # Next 5 students paid partial
        elif idx < 10:
            db.payments.insert_one({
                'fee_id': h_fee_id,
                'student_id': stu['id'],
                'amount': 25000.0,
                'payment_date': (date.today() - timedelta(days=15)).isoformat(),
                'mode': 'UPI',
                'receipt_number': f'REC-2024-{1000 + idx}',
                'recorded_by': warden_id,
                'created_at': datetime.now() - timedelta(days=15)
            })
            db.fees.update_one({'_id': db.fees.find_one({'student_id': stu['id'], 'fee_type': 'Hostel Fee'})['_id']}, {'$set': {'paid_amount': 25000.0, 'status': 'Partial'}})
        # Remaining 5 are Pending

        # Mess fee for first 10 students
        if idx < 10:
            m_fee_id = str(db.fees.insert_one({
                'student_id': stu['id'],
                'fee_type': 'Mess Fee',
                'amount': 20000.0,
                'paid_amount': 20000.0 if idx < 3 else 0.0,
                'due_date': '2024-11-30',
                'description': 'Semester 1 Mess Charges',
                'status': 'Paid' if idx < 3 else 'Pending',
                'created_at': datetime.now() - timedelta(days=40)
            }).inserted_id)
            if idx < 3:
                db.payments.insert_one({
                    'fee_id': m_fee_id,
                    'student_id': stu['id'],
                    'amount': 20000.0,
                    'payment_date': (date.today() - timedelta(days=20)).isoformat(),
                    'mode': 'Cash',
                    'receipt_number': f'REC-MESS-{500 + idx}',
                    'recorded_by': warden_id,
                    'created_at': datetime.now() - timedelta(days=20)
                })

    # 7. Mess Menu
    print("7. Setting up 7-day Mess Menu...")
    menu_data = [
        ('Monday', 'Idli, Sambar, Chutney, Tea/Coffee', 'Rice, Dal Tadka, Paneer Butter Masala, Roti, Salad', 'Roti, Mixed Veg Curry, Dal Fry, Rice, Gulab Jamun'),
        ('Tuesday', 'Aloo Paratha, Curd, Pickle, Tea/Coffee', 'Veg Biryani, Raita, Dal Makhani, Roti', 'Chapati, Bhindi Masala, Rasam, Rice, Fruit Custard'),
        ('Wednesday', 'Poha, Sev, Boiled Eggs / Banana, Tea', 'Rice, Rajma Masala, Roti, Curd, Papad', 'Jeera Rice, Chana Masala, Puri, Halwa'),
        ('Thursday', 'Upma, Coconut Chutney, Vada, Coffee', 'Lemon Rice, Dal Palak, Aloo Gobi, Roti', 'Roti, Egg Curry / Paneer Kadhai, Rice, Kheer'),
        ('Friday', 'Masala Dosa, Sambar, Chutney, Tea', 'Veg Pulao, Dal Fry, Mix Veg, Roti, Curd', 'Roti, Malai Kofta, Dal Tadka, Rice, Ice Cream'),
        ('Saturday', 'Puri Bhaji, Tea/Coffee', 'Khichdi, Kadhi, Papad, Aloo Jeera, Salad', 'Pav Bhaji / Fried Rice, Manchurian, Sweet'),
        ('Sunday', 'Chole Bhature, Lassi', 'Special Thali: Paneer Tikka, Naan, Dal Makhani, Pulao', 'Light Khichdi / Roti, Dal Fry, Fresh Fruit')
    ]
    for day, bf, ln, dn in menu_data:
        db.mess_menu.insert_one({
            'day': day,
            'breakfast': bf,
            'lunch': ln,
            'dinner': dn,
            'updated_at': datetime.now()
        })

    # 8. Complaints
    print("8. Creating Sample Complaints...")
    complaints_data = [
        (student_records[0]['id'], 'Plumbing', 'Bathroom tap leaking continuously in Room A-101.', 'Open', ''),
        (student_records[1]['id'], 'Electrical', 'Ceiling fan making squeaking noise at medium speed.', 'In Progress', 'Electrician assigned for tomorrow.'),
        (student_records[2]['id'], 'Internet', 'WiFi router on 2nd floor has frequent dropouts.', 'Resolved', 'Router reset and firmware updated.'),
        (student_records[3]['id'], 'Cleanliness', 'Corridor on 1st floor requires sweeping and mopping.', 'Open', ''),
        (student_records[4]['id'], 'Maintenance', 'Window latch broken, rattles during strong winds.', 'Resolved', 'Latch replaced by carpenter.')
    ]
    for sid, cat, desc, stat, rem in complaints_data:
        db.complaints.insert_one({
            'student_id': sid,
            'category': cat,
            'description': desc,
            'status': stat,
            'remarks': rem,
            'created_at': datetime.now() - timedelta(days=5)
        })

    # 9. Leave Requests
    print("9. Creating Sample Leave Requests...")
    leaves_data = [
        (student_records[0]['id'], 'Leave', (date.today() + timedelta(days=2)).isoformat(), (date.today() + timedelta(days=5)).isoformat(), 'Sister wedding ceremony at Jaipur.', 'Approved', 'Approved by warden. Have a safe journey.'),
        (student_records[1]['id'], 'Outpass', date.today().isoformat(), date.today().isoformat(), 'Medical checkup and buying textbooks.', 'Approved', 'Valid till 8:00 PM.'),
        (student_records[2]['id'], 'Leave', (date.today() + timedelta(days=7)).isoformat(), (date.today() + timedelta(days=10)).isoformat(), 'Family function at hometown.', 'Pending', '')
    ]
    for sid, ltype, fdate, tdate, reason, stat, rem in leaves_data:
        db.leaves.insert_one({
            'student_id': sid,
            'leave_type': ltype,
            'from_date': fdate,
            'to_date': tdate,
            'reason': reason,
            'status': stat,
            'remarks': rem,
            'created_at': datetime.now() - timedelta(days=1)
        })

    # 10. Visitors
    print("10. Creating Sample Visitors...")
    visitors_data = [
        ('Ramesh Sharma', student_records[0]['id'], 'Aarav Sharma', 'Parent visit & bringing winter clothes', '10:30', '13:00', date.today().isoformat()),
        ('Suresh Iyer', student_records[1]['id'], 'Ananya Iyer', 'Family meeting', '14:00', '', date.today().isoformat())
    ]
    for vname, sid, svis, purp, tin, tout, vdate in visitors_data:
        db.visitors.insert_one({
            'visitor_name': vname,
            'student_id': sid,
            'student_visited': svis,
            'purpose': purp,
            'in_time': tin,
            'out_time': tout,
            'visit_date': vdate,
            'created_at': datetime.now()
        })

    # 11. Notices
    print("11. Creating Notices...")
    notices_data = [
        ('Hostel Annual Sports Meet 2024', 'Annual sports meet will be held on the upcoming weekend. Registrations open for cricket, badminton, and table tennis at the warden office.', 'Normal', 'Prof. Rajesh Sharma'),
        ('Emergency Water Tank Maintenance', 'Water supply will be suspended on Thursday between 10:00 AM and 2:00 PM for overhead tank cleaning and chlorination.', 'High', 'Chief Administrator'),
        ('Mess Timings Revision for Winter', 'Breakfast: 7:30 AM - 9:30 AM | Lunch: 12:30 PM - 2:30 PM | Dinner: 7:30 PM - 9:30 PM starting next Monday.', 'Normal', 'Prof. Rajesh Sharma'),
        ('Strict Curfew Reminder: 10:00 PM', 'All residents must check in before 10:00 PM. Late entries require prior written outpass approval from the warden.', 'High', 'Prof. Rajesh Sharma')
    ]
    for title, content, prio, posted_by in notices_data:
        db.notices.insert_one({
            'title': title,
            'content': content,
            'priority': prio,
            'posted_by': posted_by,
            'created_at': datetime.now() - timedelta(days=2)
        })

    print("\n" + "=" * 60)
    print("  SEEDING COMPLETE SUCCESSFULLY!")
    print("=" * 60)
    print("\n[LOGIN CREDENTIALS]")
    print("-" * 50)
    print("1. ADMIN ACCOUNT:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   Role:     Full system access, blocks, rooms, reports, fees")
    print("-" * 50)
    print("2. WARDEN ACCOUNT:")
    print("   Username: warden")
    print("   Password: warden123")
    print("   Role:     Student allocations, complaints, leaves, mess, notices")
    print("-" * 50)
    print("3. STUDENT ACCOUNTS (15 accounts):")
    print("   Usernames: student1 through student15")
    print("   Password:  student123 (same for all students)")
    print("   Examples:")
    print("   - student1 (Aarav Sharma, Roll: 2024CS01, Room: A-101)")
    print("   - student2 (Ananya Iyer, Roll: 2024CS02, Room: B-101)")
    print("   - student3 (Rohan Verma, Roll: 2024ME01, Room: A-102)")
    print("=" * 60)

if __name__ == '__main__':
    seed()

