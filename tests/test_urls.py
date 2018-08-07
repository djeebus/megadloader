def test_mega_urls():
    from megadloader import decode_url
    url = decode_url('https://mega.nz/#F!m2wgnAJR!t1kLXa7x073kOAXb4PPWKw')
    assert url == 'https://mega.nz/#F!m2wgnAJR!t1kLXa7x073kOAXb4PPWKw'

    url = decode_url('aHR0cHM6Ly9tZWdhLm56LyNGIW0yd2duQUpSIXQxa0xYYTd4MDcza09BWGI0UFBXS3c=')
    assert url == 'https://mega.nz/#F!m2wgnAJR!t1kLXa7x073kOAXb4PPWKw'

    url = decode_url('''Link: aHR0cHM6Ly9tZWdhLm56LyNGIUNieGltQWdC
Key: IWQ4bEI5eUFuVWNsN0JyaE9rbnd5VEE=
''')
    assert url == 'https://mega.nz/#F!CbximAgB!d8lB9yAnUcl7BrhOknwyTA'

    url = decode_url('''M: #F!KiBG0Y6Y
K: !tZHr-4oKGpHmoVx8lpo8PA''')
    assert url == 'https://mega.nz/#F!KiBG0Y6Y!tZHr-4oKGpHmoVx8lpo8PA'

