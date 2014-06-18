from inbox.models import CleanUserProcess

RFC_822_TEST = """Delivered-To: prueba42@eforcers.com.co
Received: by 10.97.1.204 with SMTP id bi12csp118170qdd;
 Mon, 16 Jun 2014 09:29:54 -0700 (PDT)
X-Received: by 10.194.80.7 with SMTP id n7mr29762977wjx.8.1402936194243;
 Mon, 16 Jun 2014 09:29:54 -0700 (PDT)
Return-Path: <administrador@eforcers.com.co>
Received: from mail-qc0-x22b.google.com (mail-qc0-x22b.google.com
 [2607:f8b0:400d:c01::22b])
 by mx.google.com with ESMTPS id q1si8574359wiz.56.2014.06.16.09.29.53
 for <prueba42@eforcers.com.co>
 (version=TLSv1 cipher=ECDHE-RSA-RC4-SHA bits=128/128);
 Mon, 16 Jun 2014 09:29:53 -0700 (PDT)
Received-SPF: pass (google.com: domain of administrador@eforcers.com.co
 designates 2607:f8b0:400d:c01::22b as permitted sender)
 client-ip=2607:f8b0:400d:c01::22b;
Authentication-Results: mx.google.com;
 spf=pass (google.com: domain of administrador@eforcers.com.co designates
 2607:f8b0:400d:c01::22b as permitted sender)
 smtp.mail=administrador@eforcers.com.co;
 dkim=pass header.i=@eforcers.com.co
Received: by mail-qc0-f171.google.com with SMTP id w7so8213032qcr.2
 for <prueba42@eforcers.com.co>; Mon, 16 Jun 2014 09:29:52 -0700 (PDT)
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
 d=eforcers.com.co; s=google;
 h=mime-version:from:date:message-id:subject:to:content-type;
 bh=xOHG51U1bQfXNKForOA/RGTHfGZBRx+ANtm6Cbk+1uU=;
 b=G5TN4kqNJcd5R7Qof3XmGPdUT8+DQsI6e6lF4dKH3yjfnCQ/OlBbkk7kyqvmFORypq
 64GtTeHVtAea/+EN21dc7MIB/+Y3VetbPkJ64UcnMQHaDWmQoZp2BDPYf2ED7xwdnE5s
 iegoSY91EYugMqX1i1Jn2htmO/ETL1oMHzrUU=
X-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;
 d=1e100.net; s=20130820;
 h=x-gm-message-state:mime-version:from:date:message-id:subject:to
 :content-type;
 bh=xOHG51U1bQfXNKForOA/RGTHfGZBRx+ANtm6Cbk+1uU=;
 b=KhrSfzLZZj8n4/SyoPdgZQiO8nhLQrckF3AfwfZfix6+QG27R4PD5yZuzkjwSUVXlw
 X6JCAu1vuKbcVOEp3LFBuZ0SlqpKU2neFTQANi94+tBuaDtjvo4ZrbrdzXkP/qUUhVvY
 pVFtp9uX4j+SV7IbKveox54Jh1WtB6JzXDwe9rPEAKB+t+jTQNzNiQPM1ko0oSUfZpJL
 sCnBm10MowijUHa2Nb5ERp11SFm2zw0ePw+gDEV4dKQXnput/seZW06BKr3fcQvxy+OM
 ZPlhFB7ZfWojX0jXIjEmpN5wJ0hdRZJ0aZYW1O48Lqg5RcRZCtCk7byTuFR6kM9E5+Uu
 Esaw==
X-Gm-Message-State: ALoCoQmLGxMYgI+/15LxPyb+6sunpjFEnqClfEt7jXeRAOhbz9qeezx0yjAqFzupFRdGRl8UipBL
X-Received: by 10.140.51.172 with SMTP id u41mr26588426qga.69.1402936192559;
 Mon, 16 Jun 2014 09:29:52 -0700 (PDT)
MIME-Version: 1.0
Received: by 10.229.52.3 with HTTP; Mon, 16 Jun 2014 09:29:12 -0700 (PDT)
From: "Dominio, Administrador" <administrador@eforcers.com.co>
Date: Mon, 16 Jun 2014 11:29:12 -0500
Message-ID: <CACzs2Q-u-9BO0ZV_q9+X_DRSwrTj_v16MtGLeoSR5O-e6gTSMA@mail.gmail.com>
Subject: pruebamigration-uniquehash-34lkj3lk5j3l4kj3lk4j
To: Prueba 42 <prueba42@eforcers.com.co>
Content-Type: multipart/mixed; boundary=001a113517d266b8f004fbf68952

--001a113517d266b8f004fbf68952
Content-Type: multipart/alternative; boundary=001a113517d266b8e404fbf68950

--001a113517d266b8e404fbf68950
Content-Type: text/plain; charset=ISO-8859-1









--001a113517d266b8e404fbf68950
Content-Type: text/html; charset=ISO-8859-1
Content-Transfer-Encoding: quoted-printable






















--001a113517d266b8e404fbf68950--
--001a113517d266b8f004fbf68952


--001a113517d266b8f004fbf68952
Content-Type: text/html; charset="us-ascii"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit

<a href="https://doc-0k-cc-docs.googleusercontent.com/docs/securesc/7qsiir58iuo228cm7a550usjb9dj53bt/f8mfg9mhgl3ca1nnr14o4gatc5skp2d3/1402934400000/05100748793407378494/05100748793407378494/0B-n-lQ61kkE1dFQ4WHlZeDh5Y3c?h=11121655459724438378&e=download&gd=true">12-06-2014.zip</a>
--001a113517d266b8f004fbf68952--

"""

IMAP_MESSAGE = [('10 (UID 59 RFC822 {6326}', 'Delivered-To: prueba42@eforcers.com.co\r\nReceived: by 10.97.1.204 with SMTP id bi12csp278717qdd;\r\n        Wed, 18 Jun 2014 08:34:25 -0700 (PDT)\r\nX-Received: by 10.180.72.15 with SMTP id z15mr6069983wiu.46.1403105665441;\r\n        Wed, 18 Jun 2014 08:34:25 -0700 (PDT)\r\nReturn-Path: <administrador@eforcers.com.co>\r\nReceived: from mail-qg0-x22d.google.com (mail-qg0-x22d.google.com [2607:f8b0:400d:c04::22d])\r\n        by mx.google.com with ESMTPS id bp18si17112739wib.82.2014.06.18.08.34.24\r\n        for <prueba42@eforcers.com.co>\r\n        (version=TLSv1 cipher=ECDHE-RSA-RC4-SHA bits=128/128);\r\n        Wed, 18 Jun 2014 08:34:25 -0700 (PDT)\r\nReceived-SPF: pass (google.com: domain of administrador@eforcers.com.co designates 2607:f8b0:400d:c04::22d as permitted sender) client-ip=2607:f8b0:400d:c04::22d;\r\nAuthentication-Results: mx.google.com;\r\n       spf=pass (google.com: domain of administrador@eforcers.com.co designates 2607:f8b0:400d:c04::22d as permitted sender) smtp.mail=administrador@eforcers.com.co;\r\n       dkim=pass header.i=@eforcers.com.co\r\nReceived: by mail-qg0-f45.google.com with SMTP id 63so888949qgz.4\r\n        for <prueba42@eforcers.com.co>; Wed, 18 Jun 2014 08:34:24 -0700 (PDT)\r\nDKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;\r\n        d=eforcers.com.co; s=google;\r\n        h=mime-version:from:date:message-id:subject:to:content-type;\r\n        bh=RjBlkRYlX9DBjpLc/qNd70iCgp4RGVnpG/+JOiJqIso=;\r\n        b=h7K5ra/t9kF/D7Ajns2D+sQZ9ZHmIBpF1DCCzolbgStPQ4Rb9mcfe+Oj/shZLkSCjy\r\n         mPPsWjMomOYGvttzOzwS+PGSNSDMY+AuZHt8WK8k29jRV0NJ8q1OWm3O56LfiEV8Uauv\r\n         UxqTKNSYvzXTZOJvFuO4Qr1GasvrnzFz8q/K0=\r\nX-Google-DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;\r\n        d=1e100.net; s=20130820;\r\n        h=x-gm-message-state:mime-version:from:date:message-id:subject:to\r\n         :content-type;\r\n        bh=RjBlkRYlX9DBjpLc/qNd70iCgp4RGVnpG/+JOiJqIso=;\r\n        b=TGPz9KXgBxW1bbWV3/8sfsXYTCE+Ac0KMirVK0s8ZPw0QiYnFZKRh2FyY2De4Sv2jp\r\n         oZWmidib4bmoksphxeQVaUrr9F72oegOvTHWNN4naM0S52OqQ402TxhOK2iO9g1CzafG\r\n         nC8byRH+EoZnjl8SaeDP2yA9g/IBtnuSiY14bxHPjfw5/1le21sj+bmSUivYI8NqaVic\r\n         NBT2fOuCOqqGZD7oesuUv53+xOXG72lQsu93toFCWiiuPxp6WL1b7jV96c7isRx8fb4z\r\n         oPpoFh6HLwlcmCjpfOAAKOiL18F+MrgATOSFnTMzZmqCesPRSGRbPCmunz8RkCTIye1X\r\n         BkIQ==\r\nX-Gm-Message-State: ALoCoQnnUTZ2ETH89AvhJQ6S44qzXTsZXgU0nAmVqBqdc3LPfH4X4bn2G2m1iiqrjwdFkfsu+6s6\r\nX-Received: by 10.140.51.172 with SMTP id u41mr3898487qga.69.1403105663757;\r\n Wed, 18 Jun 2014 08:34:23 -0700 (PDT)\r\nMIME-Version: 1.0\r\nReceived: by 10.229.52.3 with HTTP; Wed, 18 Jun 2014 08:33:43 -0700 (PDT)\r\nFrom: "Dominio, Administrador" <administrador@eforcers.com.co>\r\nDate: Wed, 18 Jun 2014 10:33:43 -0500\r\nMessage-ID: <CACzs2Q_VcQvsijk9zckz6K8d0ma9txxLFsuRfnDSN_hQ4xXnOg@mail.gmail.com>\r\nSubject: robin\r\nTo: Prueba 42 <prueba42@eforcers.com.co>\r\nContent-Type: multipart/mixed; boundary=001a113517d2aefd0b04fc1dfec7\r\n\r\n--001a113517d2aefd0b04fc1dfec7\r\nContent-Type: multipart/alternative; boundary=001a113517d2aefd0704fc1dfec5\r\n\r\n--001a113517d2aefd0704fc1dfec5\r\nContent-Type: text/plain; charset=ISO-8859-1\r\n\r\nasdf\r\na\r\nsd\r\n fa\r\nsdf\r\n *Administrador Dominio*\r\nAdministrador\r\nadministrador@eforcers.com.co\r\n(+571) 622 8320 Ext. 12345678\r\nGoogle Apps Certified Deployment Specialist\r\n\r\n--001a113517d2aefd0704fc1dfec5\r\nContent-Type: text/html; charset=ISO-8859-1\r\nContent-Transfer-Encoding: quoted-printable\r\n\r\n<div dir=3D"ltr">asdf<div>a</div><div>sd</div><div>=A0fa</div><div>sdf<br c=\r\nlear=3D"all"><div><table border=3D"0" cellpadding=3D"0" cellspacing=3D"0"><=\r\ntbody style=3D"font-family:arial,sans-serif"><tr><td style=3D"vertical-alig=\r\nn:top"><img border=3D"0" src=3D"https://sites.google.com/a/eforcers.com/efc=\r\ni-firma-de-correo/_/rsrc/1369255368817/home/google-apps-certified-deploymen=\r\nt-specialist/badge_cds_web_v2.jpg" style=3D"width:60px"> </td>\r\n\r\n<td style=3D"vertical-align:top;padding:0 10px"><font color=3D"#0b5394"><b>=\r\nAdministrador Dominio</b></font><br style=3D"font-family:arial,sans-serif">=\r\n<font style=3D"font-family:arial,sans-serif">Administrador<br><a href=3D"ma=\r\nilto:administrador@eforcers.com.co" target=3D"_blank">administrador@eforcer=\r\ns.com.co</a><br>\r\n\r\n</font><span style=3D"font-family:arial,sans-serif;font-size:small">(+571) =\r\n622 8320 Ext</span><font style=3D"font-family:arial,sans-serif">. </font><s=\r\npan style=3D"font-family:arial,sans-serif;font-size:small">12345678<br>Goog=\r\nle Apps Certified Deployment Specialist </span></td>\r\n\r\n</tr></tbody></table></div>\r\n</div></div>\r\n\r\n--001a113517d2aefd0704fc1dfec5--\r\n--001a113517d2aefd0b04fc1dfec7\r\nContent-Type: text/html; charset=US-ASCII; name="a.html"\r\nContent-Disposition: attachment; filename="a.html"\r\nContent-Transfer-Encoding: base64\r\nX-Attachment-Id: f_hwksuvk10\r\n\r\nPGhlYWQ+DQoJPGxpbmsgaHJlZj0naHR0cDovL2ZvbnRzLmdvb2dsZWFwaXMuY29tL2Nzcz9mYW1p\r\nbHk9Um9ib3RvOjQwMCw3MDAnIHJlbD0nc3R5bGVzaGVldCcgdHlwZT0ndGV4dC9jc3MnPg0KCTxs\r\naW5rIGhyZWY9ImIuY3NzIiB0eXBlPSJ0ZXh0L2NzcyIgcmVsPSdzdHlsZXNoZWV0Jz4NCg0KPC9o\r\nZWFkPg0KPGJvZHkgc3R5bGU9Im1hcmdpbjogMCBhdXRvOyB3aWR0aDo4MDBweDsgZm9udC1mYW1p\r\nbHk6ICdSb2JvdG8nIj4NCgk8aDE+UGFyZW50IFBhZ2UgVGl0bGU8L2gxPg0KCTxpZnJhbWUgc3Jj\r\nPSJodHRwOi8vbG9jYWxob3N0OjgwODAvZWFnYS9hL2Vmb3JjZXJzLmNvbS5jby8iIHdpZHRoPSI4\r\nMDAiIGhlaWdodD0iNDAwIiBmcmFtZWJvcmRlcj0iMCIgaWQ9ImNsb3Vka2V5Ij48L2lmcmFtZT4N\r\nCgk8ZGl2IGlkPSJjbG91ZGtleSI+PC9kaXY+DQoJPHNjcmlwdCB0eXBlPSJ0ZXh0L2phdmFzY3Jp\r\ncHQiPg0KCS8vIHZhciBfY2xvdWRrZXlVcmwgPSAiaHR0cDovL2xvY2FsaG9zdDo4MDgwL2VhZ2Ev\r\nYS9lZm9yY2Vycy5jb20uY28vdXNlci9sb2dpbj9uYW1lc3BhY2U9ZWZvcmNlcnMuY29tLmNvJmRl\r\nY29yYXRvcj1lbWJlZGRlZCI7DQoJLy8gdmFyIF9jayA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQo\r\nJ3NjcmlwdCcpOyBfY2sudHlwZSA9ICd0ZXh0L2phdmFzY3JpcHQnOyBfY2suYXN5bmMgPSB0cnVl\r\nOw0KIC8vICAgIF9jay5zcmMgPSAiaHR0cDovL2xvY2FsaG9zdDo4MDgwL2VhZ2Evc3RhdGljL2Vt\r\nYmVkLmpzIjsNCiAvLyAgICB2YXIgcyA9IGRvY3VtZW50LmdldEVsZW1lbnRzQnlUYWdOYW1lKCdz\r\nY3JpcHQnKVswXTsgcy5wYXJlbnROb2RlLmluc2VydEJlZm9yZShfY2ssIHMpOw0KCTwvc2NyaXB0\r\nPg0KCTxzY3JpcHQgdHlwZT0idGV4dC9qYXZhc2NyaXB0Ij4NCgkvLyBQYXJlbnQNCgkvLyB2YXIg\r\naWZyYW1lID0gZG9jdW1lbnQuZ2V0RWxlbWVudEJ5SWQoJ2Nsb3Vka2V5Jyk7DQoJLy8gaWZyYW1l\r\nLm9ubG9hZCA9IGZ1bmN0aW9uKCkgew0KCS8vIAlpZnJhbWUuY29udGVudFdpbmRvdy5wb3N0TWVz\r\nc2FnZSgnc3VwJywgJyonKTsNCgkvLyAJY29uc29sZS5sb2coaWZyYW1lLmNvbnRlbnRXaW5kb3cp\r\nCQ0KCS8vIH0NCgkNCgk8L3NjcmlwdD4NCg==\r\n--001a113517d2aefd0b04fc1dfec7--\r\n'), ' FLAGS (\\Seen))']


def add_example_clean_process_user(
        process_name='process1',
        owner_email='test@test.co',
        source_email='test@test.co',
        source_password='qwerty1234',
        destination_message_email='test@test.co',
        search_criteria=''):
    return CleanUserProcess(
        process_name=process_name,
        owner_email=owner_email,
        source_email=source_email,
        source_password=source_password,
        destination_message_email=destination_message_email,
        search_criteria=search_criteria
    ).put()

def add_example_clean_process_users(amount=25):
    process_keys = []
    for i in xrange(0, amount):
        process_keys.append(add_example_clean_process_user(
            process_name='process%s' % i))