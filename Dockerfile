FROM python:3.6.10-alpine3.10

RUN pip3 install pygithub==1.47

COPY check_pr_lables.py /check_pr_lables.py

ENTRYPOINT ["/check_pr_lables.py"]
