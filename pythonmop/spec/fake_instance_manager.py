# dict of dict, key is spec_name, value is dict of class_name and FakeClass instance
fake_instances_per_spec = {}

def create_fake_class(class_name, spec_name):
    if spec_name not in fake_instances_per_spec:
        fake_instances_per_spec[spec_name] = {}

    fake_instances = fake_instances_per_spec[spec_name]

    if class_name not in fake_instances:
        FakeClass = type(f'FakeInstanceFor_{class_name}', (object,), {})
        fake_instances[class_name] = FakeClass()
    return fake_instances[class_name]


def get_fake_class_instance(class_name, spec_name):
    fake_instances = fake_instances_per_spec.get(spec_name, {})
    ret = None
    if class_name in fake_instances:
        ret = fake_instances[class_name]
    elif 'FakeInstanceFor_' in class_name:
        # find the FakeInstanceFor_ and remove it
        class_name = ''.join(class_name.split('FakeInstanceFor_')[1:])
        ret = fake_instances[class_name]
    return ret
