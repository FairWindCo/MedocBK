from rsa import newkeys


def save_file(key, private_key=True):
    file_name = 'private.pem' if private_key else 'public.pem'
    file = open(file_name, 'wt')
    try:
        file.write(key.save_pkcs1("PEM"))
    finally:
        file.close()


if __name__ == "__main__":
    public, private = newkeys(1024)
    save_file(public, False)
    save_file(private, True)

