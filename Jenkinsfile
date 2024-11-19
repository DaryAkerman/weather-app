pipeline {
    agent {
        kubernetes {
            label "weather-app-agent"
            idleMinutes 5
            yamlFile 'build-pod.yaml'
            defaultContainer 'ez-docker-helm-build'
        }
    }
    environment {
        DOCKER_IMAGE = 'winterzone2/weather-app'
        GITHUB_API_URL = 'https://api.github.com'
        GITHUB_REPO = 'DaryAkerman/weather-app'
        GITHUB_TOKEN = credentials('github-token')
    }

    stages {
        stage("Checkout code") {
            steps {
                checkout scm
            }
        }

        stage("Prepare environment") {
            steps {
                // Fetch the full Git history to ensure origin/main is available
                script {
                    sh """
                        git fetch --no-tags --prune --progress origin +refs/heads/*:refs/remotes/origin/*
                        git checkout ${env.BRANCH_NAME}
                    """
                }
            }
        }

        stage("Check for meaningful changes") {
            steps {
                script {
                    def changes = sh(script: "git diff --name-only origin/${env.BRANCH_NAME} HEAD", returnStdout: true).trim()
                    if (changes == 'applic/values.yaml') {
                        echo "Only values.yaml was modified, skipping build."
                        currentBuild.result = 'SUCCESS'
                        return
                    } else {
                        echo "Detected meaningful changes: ${changes}"
                    }
                }
            }
        }

        stage("Build docker image") {
            steps {
                script {
                    dockerImage = docker.build("${DOCKER_IMAGE}:latest", "--no-cache .")
                    dockerImage.tag("1.0.${env.BUILD_NUMBER}")
                }
            }
        }

        stage('Push Docker image') {
            when {
                branch 'main'
            }
            steps {
                script {
                    docker.withRegistry('https://registry.hub.docker.com', 'docker-creds') {
                        dockerImage.push("latest")
                        dockerImage.push("1.0.${env.BUILD_NUMBER}")
                    }
                }
            }
        }

        stage('Update Helm values.yaml') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
                    script {
                        def valuesFilePath = "applic/values.yaml"
                        
                        // Read and modify values.yaml
                        def valuesYaml = readFile(valuesFilePath)
                        def updatedYaml = valuesYaml.replaceAll(/(?<=tag: ).*/, "\"1.0.${env.BUILD_NUMBER}\"")
                        writeFile(file: valuesFilePath, text: updatedYaml)

                        // Commit and push changes to GitHub
                        sh """
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@example.com"
                            git add ${valuesFilePath}
                            git commit -m "Update Helm chart image tag to 1.0.${env.BUILD_NUMBER}"
                            git push https://$GITHUB_TOKEN@github.com/${GITHUB_REPO}.git HEAD:${env.BRANCH_NAME}
                        """
                    }
                }
            }
        }

        stage('Create merge request') {
            when {
                not {
                    branch 'main'
                }
            }
            steps {
                withCredentials([string(credentialsId: 'github-token', variable: 'GITHUB_TOKEN')]) {
                    script {
                        def branchName = env.BRANCH_NAME
                        def pullRequestTitle = "Merge ${branchName} into main"
                        def pullRequestBody = "Automatically generated merge request for branch ${branchName}"

                        sh """
                            curl -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
                            -d '{ "title": "${pullRequestTitle}", "body": "${pullRequestBody}", "head": "${branchName}", "base": "main" }' \
                            ${GITHUB_API_URL}/repos/${GITHUB_REPO}/pulls
                        """
                    }
                }
            }
        }
    }
}
