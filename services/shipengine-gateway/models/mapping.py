shipment_status_mapping = {
    'pending': 'Pending',
    'label_purchased': 'Label Purchased',
    'cancelled': 'Canceled'
}

tracking_status_mapping = {
    'in_transit': 'In Transit'
}

label_status_mapping = {
    'completed': 'Completed'
}


def mapped_value(mapping, value):
    if value is None:
        return 'n/a'

    val = mapping.get(value, 'n/a')
    return val
