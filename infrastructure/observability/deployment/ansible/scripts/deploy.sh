#!/bash
ENV=$1
VERSION=$2
if [ -z "$ENV" ] || [ -z "$VERSION" ]; then
    echo "Usage: ./deploy.sh <dev|stage|prod> <version>"
    exit 1
fi
ansible-playbook -i inventory/$ENV.ini playbooks/setup_env.yml -e "app_version=$VERSION"
