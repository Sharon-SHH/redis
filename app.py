from celery import Celery, Task
from flask import Flask, request, jsonify
from tasks import add_together

app = Flask(__name__)
app.config.from_mapping(
    CELERY=dict(
        broker_url='redis://localhost:6379/0',
        result_backend='redis://localhost:6379/1',
        task_ignore_result=False,
    ),
)


def make_celery(app: Flask) -> Celery:
    celery = Celery(
        app.import_name,
        broker=app.config["CELERY"]["broker_url"],
        backend=app.config["CELERY"]["result_backend"]
    )
    celery.conf.update(app.config)

    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = FlaskTask
    return celery


celery_app = make_celery(app)

@app.route('/')
def index():
    return "Hello, World!"


@app.route("/add", methods=['POST'])
def add():
    data = request.json
    x = data.get('x')
    y = data.get('y')
    task = add_together.delay(x, y)
    return jsonify({'task_id': task.id}), 202

@app.route('/result/<task_id>')
def result(task_id):
    task = add_together.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Task pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'result': task.result
        }
    else:
        response = {
            'state': task.state,
            'status': str(task.info)  # Exception message
        }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5001)