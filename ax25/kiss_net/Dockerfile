FROM python:2.7-alpine
#RUN mkdir /code
#ADD kiss_net_playback.py /code
#ADD 20180318_023352.kiss /code
ADD . /code
WORKDIR /code
#RUN pip install -r requirements.txt
#CMD ["python", "kiss_net_playback.py --kiss_file ./20180318_023352.kiss"]
CMD ["python", "kiss_net_playback.py", "--kiss_file", "20180318_023352.kiss"]
