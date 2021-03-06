# coding:utf-8
import time
import logging
logger = logging.getLogger("mail")

from protocol import poem_pb
import protocol.poem_pb as msgid

from yy.rpc import RpcService
from yy.rpc import rpcmethod
from yy.message.header import fail_msg
from yy.message.header import success_msg

from config.configs import get_config
from config.configs import MailConfig
from reward.manager import build_reward_msg


class MailService(RpcService):

    @rpcmethod(msgid.MAIL_LIST)
    def mail_list(self, msgtype, body):
        req = poem_pb.MailListRequest()
        req.ParseFromString(body)
        player = self.player
        mails = sorted(player.mails.values(), key=lambda s: s.addtime)
        rsp = poem_pb.MailList()
        now = int(time.time())
        # 删除过期邮件
        pending = []
        for mail in mails:
            if mail.cd and now > mail.addtime + mail.cd:
                if mail.isread and mail.isreceived:
                    pending.append(mail)
            else:
                data = {}
                config = get_config(MailConfig).get(mail.configID)
                if config:
                    data.update(**config._asdict())
                data.update(
                    mailID=mail.mailID,
                    title=mail.title,
                    type=mail.type,
                    content=mail.content,
                    cd=mail.cd - (now - mail.addtime),
                    isread=mail.isread,
                    isreceived=mail.isreceived,
                    addtime=mail.addtime,
                )
                each = rsp.mails.add(**data)
                tmp_transform = {
                    500026: 800026,
                    500027: 800027,
                    500028: 800028,
                    500029: 800029,
                    500030: 800030,
                    500031: 800031,
                    500032: 800032,
                    500021: 800021,
                    14000371: 21000371,
                    14000372: 21000372,
                    14000373: 21000373,
                    14000374: 21000374,
                    14000375: 21000375,
                }
                for item in mail.addition.get('matList', []):
                    item[0] = tmp_transform.get(item[0], item[0])
                build_reward_msg(each, mail.addition)
        if pending:
            player.del_mails(*pending)
            logger.debug("newmailcount %r", player.newmailcount)
            player.save()
            player.sync()
        return success_msg(msgtype, rsp)

    @rpcmethod(msgid.MAIL_READ)
    def mail_read(self, msgtype, body):
        p = self.player
        req = poem_pb.ReadMailConetent()
        req.ParseFromString(body)
        mail = p.mails.get(req.mailID)
        rsp = poem_pb.ReadMailConetentResponse()
        rsp.mailID = req.mailID
        if mail:
            if not mail.cd and not mail.addition:
                p.del_mails(mail)
                rsp.delete = True
            else:
                mail.isread = True
                mail.save()
        # p.touch_mails()
        return success_msg(msgtype, rsp)

    @rpcmethod(msgid.MAIL_RECV)
    def mail_recv(self, msgtype, body):
        req = poem_pb.ReceiveMailReward()
        req.ParseFromString(body)
        player = self.player
        mail = player.mails.get(req.mailID)
        if not mail:
            return fail_msg(msgtype, reason='没有这个邮件')
        if mail.playerID != player.entityID:
            return fail_msg(msgtype, reason='没有这个邮件')
        if mail.isreceived:
            return fail_msg(msgtype, reason='已经领取过了')
        from reward.manager import apply_reward
        from reward.constants import RewardType
        tmp_transform = {
            500026: 800026,
            500027: 800027,
            500028: 800028,
            500029: 800029,
            500030: 800030,
            500031: 800031,
            500032: 800032,
            500021: 800021,
            14000371: 21000371,
            14000372: 21000372,
            14000373: 21000373,
            14000374: 21000374,
            14000375: 21000375,
        }
        for item in mail.addition.get('matList', []):
            item[0] = tmp_transform.get(item[0], item[0])
        apply_reward(player, mail.addition, type=RewardType.Mail)
        rsp = poem_pb.ReceiveMailRewardResponse()
        rsp.mailID = req.mailID
        flag = False
        if not mail.cd:
            player.del_mails(mail)
            rsp.delete = True
        else:
            flag = True
            mail.isreceived = True
            mail.save()
        if flag:
            player.touch_mails()
        player.save()
        player.sync()
        return success_msg(msgtype, rsp)

    @rpcmethod(msgid.MAIL_ONEKEY_RECV)
    def mail_onekey_recv(self, msgtype, body):
        from reward.manager import apply_reward
        from reward.constants import RewardType
        player = self.player
        flag = False
        for mail in player.mails.values():
            if not mail.isreceived:
                tmp_transform = {
                    500026: 800026,
                    500027: 800027,
                    500028: 800028,
                    500029: 800029,
                    500030: 800030,
                    500031: 800031,
                    500032: 800032,
                    500021: 800021,
                    14000371: 21000371,
                    14000372: 21000372,
                    14000373: 21000373,
                    14000374: 21000374,
                    14000375: 21000375,
                }
                for item in mail.addition.get('matList', []):
                    item[0] = tmp_transform.get(item[0], item[0])
                if mail.addition:
                    apply_reward(player, mail.addition, type=RewardType.Mail)
            flag = True
            mail.isreceived = True
            mail.isread = True
            mail.save()
        mails = []
        for mail in player.mails.values():
            if not mail.cd and mail.isreceived:
                mails.append(mail)
        if flag:
            player.touch_mails()
        player.del_mails(*mails)
        player.save()
        player.sync()
        return success_msg(msgtype, '')
