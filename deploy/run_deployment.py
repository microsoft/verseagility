import sys
from service import deploy_service

if __name__ == '__main__':
    deploy_service(do_deploy=True, project_name='mbio_en', ws=None)