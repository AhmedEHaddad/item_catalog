#!/usr/bin/python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, User, Book

engine = create_engine('sqlite:///itemcatalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create first user
user1 = User(name='admin', email='leandrikuyk@gmail.com')

session.add(user1)
session.commit()

# Create list of books organized by category
book1 = Book(name="The Girl with the Dragon Tattoo",
             description="""Murder mystery, family saga,
             love story, and financial intrigue combine
             into one satisfyingly complex and entertainingly
             atmospheric novel""", author="Stieg Larsson",
             categories="Mystery",
             cover="https://images.gr-assets.com/books/1327868566l/2429135.jpg",
             user_id=1)

session.add(book1)
session.commit()

book2 = Book(name="Harry Potter and the Sorcerer's Stone",
             description="""Rescued from the outrageous
             neglect of his aunt and uncle, a young boy
             with a great destiny proves his worth while
             attending Hogwarts School for Wizards and Witches.""",
             author="J.K. Rowling", categories="Fantasy",
             cover="https://images-na.ssl-images-amazon.com/images/I/81iqZ2HHD-L.jpg",
             user_id=1)

session.add(book2)
session.commit()

book3 = Book(name="The Time Traveler's Wife",
             description="""Passionately in love,
             Clare and Henry vow to hold onto each
             other and their marriage as they struggle
             with the effects of Chrono-Displacement
             Disorder, a condition that casts Henry
             involuntarily into the world of time
             travel.""", author="Audrey Niffenegger",
             categories="Romance",
             cover="https://pictures.abebooks.com/VANDELLOBOOKS/18082528571.jpg",
             user_id=1)

session.add(book3)
session.commit()

book4 = Book(name="Bird Box", description="""Something
             is out there, something you can not see.
             Something you must not see, because one
             glimpse will drive you violently insane""",
             author="Josh Malerman", categories="Horror",
             cover="https://images-na.ssl-images-amazon.com/images/I/81SRiprjQSL.jpg",
             user_id=1)

session.add(book4)
session.commit()

book5 = Book(name="Everything, Everything",
             description="""This innovative, heartfelt debut
             novel tells the story of a girl who is literally
             allergic to the outside world. When a new family
             moves in next door, she begins a complicated romance
             that challenges everything she is ever known.""",
             author="Nicola Yoon", categories="Fiction",
             cover="http://2.bp.blogspot.com/-nKfBook8_9g/VJMM4HkUySI/AAAAAAAAC2A/_oSkXCo0EN8/s1600/EverythingEverythingCover.jpg",
             user_id=1)

session.add(book5)
session.commit()

book6 = Book(name="The Perks of Being a Wallflower",
             description="""This is the story of what
             it is like to grow up in high school. More
             intimate than a diary, Charlies letters are
             singular and unique, hilarious and devastating.
             We may not know where he lives. We may not know
             to whom he is writing. All we know is the world
             he shares.""", author="Stephen Chbosky",
             categories="Fiction",
             cover="https://prodimage.images-bn.com/pimages/9781451696196_p0_v2_s550x406.jpg",
             user_id=1)

session.add(book6)
session.commit()


print 'Successfully populated database'
