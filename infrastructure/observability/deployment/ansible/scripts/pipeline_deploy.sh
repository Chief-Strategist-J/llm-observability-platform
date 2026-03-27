#!/bash
ACTION=$1
ENV=$2
VERSION=$3
if [ -z "$ACTION" ]; then
    echo "Usage: ./pipeline_deploy.sh <deploy|smoke|promote> <env> <version>"
    exit 1
fi
case $ACTION in
    deploy)
        ./scripts/hybrid_deploy.sh $ENV $VERSION
        ;;
    smoke)
        ansible-playbook -i inventory/$ENV.ini playbooks/smoke_test.yml -e "app_version=$VERSION"
        ;;
    promote)
        ansible-playbook playbooks/promote.yml -e "staging_tag=$VERSION" -e "prod_tag=$VERSION-stable"
        ;;
    *)
        echo "Unknown action: $ACTION"
        exit 1
        ;;
esac
