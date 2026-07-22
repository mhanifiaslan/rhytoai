from kerykeion import AstrologicalSubject, ReportGenerator

def get_natal_chart(name: str, year: int, month: int, day: int, hour: int, minute: int, city: str, nation: str):
    subject = AstrologicalSubject(name, year, month, day, hour, minute, city=city, nation=nation)
    # Using the Kerykeion ReportGenerator functionality
    report_gen = ReportGenerator(subject)
    report_text = report_gen.generate_report()
    
    # Return structured dict of the astrological data
    return {
        "sun": {
            "sign": subject.sun.sign,
            "position": subject.sun.position,
        },
        "moon": {
            "sign": subject.moon.sign,
            "position": subject.moon.position,
        },
        "ascendant": {
            "sign": subject.first_house.sign,
            "position": subject.first_house.position,
        },
        "report_summary": "Astrological generation successful"
    }
