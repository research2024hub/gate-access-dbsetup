# Importing soft_delete registers the "hide soft-deleted rows" query hook.
from app.db import soft_delete  # noqa: F401

from app.db.models.account_holder import AccountHolder
from app.db.models.account_type import AccountType
from app.db.models.estate import Estate
from app.db.models.event import Event
from app.db.models.event_register import EventRegister
from app.db.models.guest import Guest
from app.db.models.log import Log
from app.db.models.personal_info import PersonalInfo
from app.db.models.privilege import Privilege
from app.db.models.user import User
from app.db.models.vehicle import Vehicle
from app.db.models.gate import Gate
from app.db.models.access_group import AccessGroup
from app.db.models.face import Face
from app.db.models.gate_access_group_link import GateAccessGroupLink
from app.db.models.account_type_privilege_link import AccountTypePrivilegeLink
from app.db.models.pending_user import PendingUser
from app.db.models.personal_info_gate_link import PersonalInfoGateLink
from app.db.models.personal_info_privilege_link import PersonalInfoPrivilegeLink
from app.db.models.pending_account_holder import PendingAccountHolder
from app.db.models.metrics import SystemMetric
from app.db.models.accesslog import Accesslog
from app.db.models.message import Message
from app.db.models.report import Report
from app.db.models.report_status import ReportStatus

from app.db.models import indexes  # noqa: F401
