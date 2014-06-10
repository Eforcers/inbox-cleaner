from inbox.models import CleanUserProcess

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