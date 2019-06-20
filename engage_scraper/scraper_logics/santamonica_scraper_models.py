import psycopg2
import sqlalchemy
from sqlalchemy import Column, String, Integer, Text, Sequence, Float, ForeignKey, Boolean, Table
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
    location_lat = Column(Float, nullable=False, default=34.024212)
    location_lng = Column(Float, nullable=False, default=-118.496475)


class Agenda(Base):
    __tablename__ = "ingest_agenda"
    id = Column(Integer, Sequence("ingest_agenda_id_seq"), primary_key=True)
    meeting_time = Column(Integer)  # Unix timestamp
    committee_id = Column(ForeignKey("ingest_committee.id", ondelete='CASCADE'))
    meeting_id = Column(String(20), nullable=False)  # Agenda ID
    processed = Column(Boolean, default=False)


tag_association_table = Table('ingest_agendaitem_tags', Base.metadata,
                              Column('agendaitem_id', Integer,
                                     ForeignKey('ingest_agendaitem.id')),
                              Column('tag_id', Integer, ForeignKey('ingest_tag.id')))


class AgendaItem(Base):
    __tablename__ = "ingest_agendaitem"
    id = Column(Integer, Sequence('ingest_agendaitem_id_seq'), primary_key=True)
    title = Column(Text, nullable=False)
    department = Column(String(250), nullable=True)
    body = Column(ARRAY(Text), nullable=False)
    sponsors = Column(String(250), nullable=True)
    agenda_id = Column(ForeignKey("ingest_agenda.id", ondelete="CASCADE"))
    meeting_time = Column(Integer)  # Unix timestamp
    agenda_item_id = Column(String(20), nullable=False)
    # tags = relationship("Tag", secondary=tag_association_table)

class AgendaRecommendation(Base):
    __tablename__ = "ingest_agendarecommendation"
    id = Column(Integer, Sequence('ingest_agendarecommendation_id_seq'), primary_key=True)
    agenda_item_id = Column(ForeignKey("ingest_agendaitem.id", ondelete="CASCADE"))
    recommendation = Column(ARRAY(Text))


class CommitteeMember(Base):
    __tablename__ = "ingest_committeemember"
    id = Column(Integer, Sequence('ingest_committeemember_id_seq'), primary_key=True)
    firstname = Column(String(250))
    lastname = Column(String(250))
    email = Column(String(250))
    committee_id = Column(ForeignKey("ingest_committee.id", ondelete="CASCADE"))
