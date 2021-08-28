import qrcode


def main(filename: str) -> None:
    url = "https://docs.google.com/forms/d/e/1FAIpQLScINBBBmvQym89K_gBWYayGBq23-RYZs8RrrnumBckf9lhvMg/viewform"
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5,
    )
    qr.add_data(data=url)
    qr.make(fit=True)
    img = qr.make_image(fill="black", back_color="white")
    img.save(filename)


if __name__ == "__main__":
    main(filename="nominations_qr.png")