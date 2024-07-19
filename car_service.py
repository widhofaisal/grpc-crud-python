import grpc
from concurrent import futures
import cars_pb2
import cars_pb2_grpc
import psycopg2
from datetime import datetime
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

class CarService(cars_pb2_grpc.CarServiceServicer):

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        self.cursor = self.conn.cursor()

    def CreateCar(self, request, context):
        self.cursor.execute("""
            INSERT INTO cars (brand, date_created, date_modified, last_modified_by, price, type, year)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;
        """, (request.brand, datetime.now(), datetime.now(), str(uuid.uuid4()), request.price, request.type, request.year))
        car_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return cars_pb2.Car(id=car_id, brand=request.brand, date_created=str(datetime.now()), date_modified=str(datetime.now()), last_modified_by=str(uuid.uuid4()), price=request.price, type=request.type, year=request.year)

    def GetCar(self, request, context):
        self.cursor.execute("SELECT * FROM cars WHERE id = %s", (request.id,))
        car = self.cursor.fetchone()
        if car:
            return cars_pb2.Car(id=car[0], brand=car[1], date_created=str(car[2]), date_modified=str(car[3]), last_modified_by=car[4], price=car[5], type=car[6], year=car[7])
        else:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details('Car not found')
            return cars_pb2.Car()

    def UpdateCar(self, request, context):
        self.cursor.execute("""
            UPDATE cars SET brand = %s, date_modified = %s, last_modified_by = %s, price = %s, type = %s, year = %s
            WHERE id = %s;
        """, (request.brand, datetime.now(), str(uuid.uuid4()), request.price, request.type, request.year, request.id))
        self.conn.commit()
        return request

    def DeleteCar(self, request, context):
        self.cursor.execute("DELETE FROM cars WHERE id = %s", (request.id,))
        self.conn.commit()
        return cars_pb2.CarId(id=request.id)

    def ListCars(self, request, context):
        print("masuk ListCars")
        self.cursor.execute("SELECT * FROM cars")
        print("self:", self)
        print("masuk ListCars 2")
        cars = self.cursor.fetchall()
        print(cars)
        car_list = cars_pb2.CarList()
        for car in cars:
            car_list.cars.append(cars_pb2.Car(id=car[0], brand=car[1], date_created=str(
                car[2]), date_modified=str(car[3]), last_modified_by=car[4], price=car[5], type=car[6], year=car[7]))
        return car_list


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    cars_pb2_grpc.add_CarServiceServicer_to_server(CarService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    serve()
