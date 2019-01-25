from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import User, Technology, Base, TechnologyItem

engine = create_engine('postgresql://catalog:password@localhost/catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)

session = DBSession()
# the first user
User1 = User(name="SMS athher", email="smsa3r@gmail.com",
             picture='https://www.gulf-up.com/bfqx2ppwqssj')

session.add(User1)
session.commit()
# Poetry items
technology1 = Technology(user_id=1, name="Apple",
                         description="Apple Inc. is an American\
                         multinational technology company\
                         headquartered in Cupertino California\
                         that designs, develops, and sells consumer\
                         electronics, computer software, and online services")

session.add(technology1)
session.commit()

item = TechnologyItem(user_id=1, name="iPhone XR",
                      description="For a limited time, get iPhone XR\
                      from $449 or iPhone XS from $699 when you trade\
                      in your iPhone.", type="MOBILE", price="$699",
                      technology=technology1)

session.add(item)
session.commit()

item1 = TechnologyItem(user_id=1, name="MacBook Air",
                       description="Touch ID1.6GHz Dual-Core Processor\
                       Turbo Boost up to 3.6GHz 128GB Storage",
                       type="COMPUTING", price="$1,199.00",
                       technology=technology1)

session.add(item1)
session.commit()

technology2 = Technology(user_id=1, name="Samsung",
                         description="Samsung is a South Korean multinational\
                         conglomerate headquartered in Samsung Town, Seoul.\
                         It comprises numerous affiliated businesses, most\
                         of them united under the Samsung brand,and is the\
                         largest South Korean chaebol")
session.add(technology2)
session.commit()
item3 = TechnologyItem(user_id=1, name="Notebook9Pro15(256GB SSD)",
                       description="Premium, thin and light",
                       type="COMPUTING", price="$1,199.99",
                       technology=technology2)

session.add(item3)
session.commit()

item4 = TechnologyItem(user_id=1, name="Galaxy Note9",
                       description="They look like an everyday family living\
                       an ordinary life. But beyond the edges of this peaceful\
                       farm, unimaginable forces of light and dark\
                       have been unleashed",
                       type="MOBILE", price="$199.99",
                       technology=technology2)
session.add(item4)
session.commit()

technology3 = Technology(user_id=1, name="HP",
                         description="The Hewlett-Packard Company wasan\
                         American multinational information technology company\
                         headquartered in Palo Alto, California")

session.add(technology3)
session.commit()

item5 = TechnologyItem(user_id=1, name="HP EliteBook x360 1040 G5 Notebook PC",
                       description="Windows 10 Pro 64 8th Generation Intel\
                       Core i5 processor 8 GB memory; 256 GB NVMe SSD",
                       type="COMPUTING", price="$1,901.90",
                       technology=technology3)

session.add(item5)
session.commit()

item6 = TechnologyItem(user_id=1, name="HP EliteBook x360 1040 G5 Noteitem",
                       description="Windows 10 Pro 64 8th Generation Intel\
                       Core i5 processor 16 GB memory; 256 GB NVMe SSD",
                       type="COMPUTING", price="$1,901.90",
                       technology=technology3)

session.add(item6)
session.commit()

print "added category items!"
