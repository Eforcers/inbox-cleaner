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