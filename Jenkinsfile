Jenkinsfile (Declarative Pipeline)
pipeline {
    agent { docker { image 'python:3.6.7' } }
    stages {
        stage('build') {
            steps {
                echo 'Building'
                sh 'pip install -r requirements.txt'
            }
        }
        stage('test') {
            steps {
                echo 'Testing'
                sh 'python -m pytest --junitxml=./test_results.xml'
            }
            post {
                always {
                junit 'test-reports/*.xml'
                }
            }    
        }
    }
    post {
        always {
            echo 'This will always run'
        }
        success {
            echo 'This will run only if successful'
        }
        failure {
            echo 'This will run only if failed'
        }
    }
}