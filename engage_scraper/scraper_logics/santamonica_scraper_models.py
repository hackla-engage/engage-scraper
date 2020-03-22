import psycopg2
import sqlalchemy
from datetime import datetime
from sqlalchemy import Column, String, Integer, Text, Sequence, Float, ForeignKey, Boolean, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Tag(Base):
    __tablename__ = "ingest_tag"
    id = Column(Integer, Sequence("ingest_tag_id_seq"), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String)


class Committee(Base):
    __tablename__ = "ingest_committee"
    id = Column(Integer, Sequence("ingest_committee_id_seq"), primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    cutoff_offset_days = Column(Integer, default=0)
    cutoff_hour = Column(Integer, default=11)
    cutoff_minute = Column(Integer, default=59)
    location_tz = Column(String, nullable=False,
                         default="America/Los_Angeles")
    base_agenda_location = Column(
        String, nullable=False, default="http://santamonicacityca.iqm2.com/Citizens/Detail_Meeting.aspx?ID=")
    agendas_table_location = Column(
        String, nullable=False, default="https://www.smgov.net/departments/clerk/agendas.aspx")


class Agenda(Base):
    __tablename__ = "ingest_agenda"
    id = Column(Integer, Sequence("ingest_agenda_id_seq"), primary_key=True)
    meeting_time = Column(Integer)  # Unix timestamp
    committee_id = Column(ForeignKey(
        "ingest_committee.id", ondelete='CASCADE'))
    meeting_id = Column(String(20), nullable=False)  # Agenda ID
    pdf_time = Column(Integer)  # UNIX timestamp
    cutoff_time = Column(Integer)  # UNIX timestamp
    pdf_location = Column(String, nullable=True)  # static address for pdf
    processed = Column(Boolean, default=False)


tag_association_table = Table('ingest_agendaitem_tags', Base.metadata,
                              Column('agendaitem_id', Integer,
                                     ForeignKey('ingest_agendaitem.id')),
                              Column('tag_id', Integer, ForeignKey('ingest_tag.id')))


class AgendaItem(Base):
    __tablename__ = "ingest_agendaitem"
    id = Column(Integer, Sequence(
        'ingest_agendaitem_id_seq'), primary_key=True)
    title = Column(Text, nullable=False)
    department = Column(String(250), nullable=True)
    body = Column(ARRAY(Text), nullable=False)
    sponsors = Column(String(250), nullable=True)
    agenda_id = Column(ForeignKey("ingest_agenda.id", ondelete="CASCADE"))
    meeting_time = Column(Integer)  # Unix timestamp
    agenda_item_id = Column(String(20), nullable=False, unique=True)
    # tags = relationship("Tag", secondary=tag_association_table)


class AgendaRecommendation(Base):
    __tablename__ = "ingest_agendarecommendation"
    id = Column(Integer, Sequence(
        'ingest_agendarecommendation_id_seq'), primary_key=True)
    agenda_item_id = Column(ForeignKey(
        "ingest_agendaitem.id", ondelete="CASCADE"))
    recommendation = Column(ARRAY(Text))


class CommitteeMember(Base):
    __tablename__ = "ingest_committeemember"
    id = Column(Integer, Sequence(
        'ingest_committeemember_id_seq'), primary_key=True)
    firstname = Column(String(250))
    lastname = Column(String(250))
    email = Column(String(250))
    committee_id = Column(ForeignKey(
        "ingest_committee.id", ondelete="CASCADE"))


class EngageUser(Base):
    __tablename__ = "ingest_engageuser"
    id = Column(Integer, Sequence(
        'ingest_engageuser_id_seq'), primary_key=True)
    password = Column(String(128))
    last_login = Column(DateTime(timezone=True), default=datetime.utcnow())
    is_superuser = Column(Boolean, default=False)
    username = Column(String(150))
    first_name = Column(String(30))
    last_name = Column(String(150))
    is_staff = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    date_joined = Column(DateTime(timezone=True), default=datetime.utcnow())
    email = Column(String(254))


class Message(Base):
    __tablename__ = "ingest_message"
    id = Column(Integer, Sequence('ingest_message_id_seq'), primary_key=True)
    user_id = Column(ForeignKey(
        "ingest_engageuser.id", ondelete='CASCADE'))
    agenda_item_id = Column(ForeignKey(
        'ingest_agendaitem.id', ondelete='CASCADE'))
    content = Column(Text)
    committee_id = Column(ForeignKey(
        "ingest_committee.id", ondelete='CASCADE'))
    first_name = Column(String(250))
    last_name = Column(String(250))
    zipcode = Column(Integer, default=90401)
    email = Column(String(254))
    home_owner = Column(Boolean, default=False)
    business_owner = Column(Boolean, default=False)
    resident = Column(Boolean, default=False)
    works = Column(Boolean, default=False)
    school = Column(Boolean, default=False)
    child_school = Column(Boolean, default=False)
    # Keep session key so if user authenticates one message it authenticates all messages
    session_key = Column(String(100))
    # code challenge for user
    authcode = Column(String(254))
    date = Column(Integer)  # UNIX timestamp
    sent = Column(Integer)  # UNIX timestamp
    # 0 = Con, 1 = Pro, 2 = Need more info
    pro = Column(Integer)
