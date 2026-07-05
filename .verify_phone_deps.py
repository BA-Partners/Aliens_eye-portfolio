import phonenumbers
print('phonenumbers', phonenumbers.__version__)
p = phonenumbers.parse('13800138000', 'CN')
print('parse_ok', p)
print('has_number_type', hasattr(p, 'number_type'))
print('top_attrs', [x for x in dir(phonenumbers) if 'type' in x.lower() or 'valid' in x.lower()][:50])
print('number_type_val', phonenumbers.number_type(p))
print('is_possible', phonenumbers.is_possible_number(p))
print('is_valid', phonenumbers.is_valid_number(p))
try:
    from phonenumbers import carrier
    print('carrier', carrier.name_for_number(p, 'en'))
except Exception as e:
    print('carrier_err', repr(e))
try:
    from phonenumbers import geocoder
    print('geo', geocoder.description_for_number(p, 'en'))
except Exception as e:
    print('geocoder_err', repr(e))
print('done')
