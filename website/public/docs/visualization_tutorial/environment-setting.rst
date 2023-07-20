====================
Environment Setting
====================

Setup using docker
===================
You need to take the following steps to set up the visualization tool and run it on your local machine with docker

1. Make sure that `Docker <https://docs.docker.com/get-docker/>`_ is installed

2. Build the image

.. code-block:: shell

    1_docker_build_image.sh

3. Create a conatiner from the image.  *Note* at the end of the container creation, you will be asked to log into your wandb account.

.. code-block:: shell

    2_docker_create_container.sh

4. Run the conatiner. This will run the backend on port 8000, and frontend on port 3000.

.. code-block:: shell

    3_docker_run_container.sh


.. Note:: For repeated runs

   You only need to execute step 2 once, to have an image with the required dependencies. Step 3 can be repeated to create a container with updated frontend/ and backend/ code. The script will delete and overwrite an existing container, and uses the code from this repository. The last step needs to be executed every time you want to run the visualization.


Setup (Standard)
===================
You can also set up the tool without using **Docker**

- Make sure that all requirements listed in the ``/pip_requirements.txt`` are satisfied.

- For backend:

    1. Change the working directory to ``/history_visualization/backend``
    
    2. Install the dependencies for backend

    .. code-block:: shell

        pip install fastapi
        pip install "uvicorn[standard]"
        pip install argparse

    3. Run the backend sever at `localhost:8000 <http://localhost:8000/>`_.

    .. code-block:: shell

        python main.py

- For frontend:

    1. Start a new terminal

    2. Install `Node.js <https://nodejs.org/en/download>`_

    3. Download dependencies:

    .. code-block:: shell

        npm install -d 
    
    4. Run the backend sever at `localhost:3000 <http://localhost:3000/>`_

    .. code-block:: shell

        npm start


Verify correctness:
====================
To verify that everything is running correctly after executing the launching process mentioned above:

1. check `localhost:8000 <http://localhost:8000/>`_ in your browser, you should see this:

.. image:: ../images/frontend_start.png


2. check `localhost:3000 <http://localhost:3000/>`_ in your browser, you should see this:

.. image:: ../images/backend_start.png