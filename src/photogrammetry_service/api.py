def route_api(app):
    @app.route('/about')
    def about():
        return app.config['ABOUT']

    @app.route('/submit_task')
    def submit_task():
        return 'Submitted task !'
