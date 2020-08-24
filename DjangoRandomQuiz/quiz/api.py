from django.contrib.auth.models import User
from restless.dj import DjangoResource
from restless.preparers import FieldsPreparer

from .models import Topic, Question, Answer, Quiz, QuizAttempt

def check_access_token():
    """Check if access token has permission to access a particular resource. If so, the Resources will say
    "is_authenticated()"""

class TopicResource(DjangoResource):
    # TODO - Only authorize these when you are the correct user.
    # TODO - Sanitize data

    preparer = FieldsPreparer(fields={
        'id': 'id',
        'uuid': 'uuid',
        'user': 'creator.username',
        'topic': 'name',
    })

    def is_authenticated(self):
        # TODO - Turn this off. We are only turning this to True for testing.
        return True
        # Alternatively, if the user is logged into the site...
        # return self.request.user.is_authenticated()

        # Alternatively, you could check an API key. (Need a model for this...)
        # from myapp.models import ApiKey
        # try:
        #     key = ApiKey.objects.get(key=self.request.GET.get('api_key'))
        #     return True
        # except ApiKey.DoesNotExist:
        #     return False

    # GET /api/topics/
    def list(self):
        # TODO - Only show objects for a particular user.
        # return Topic.objects.filter()
        return Topic.objects.all()

    # GET /api/topics/<pk>
    def detail(self, pk):
        # You need to use "pk" and not "id" due to the implementation of DjangoResource.
        return Topic.objects.get(id=pk)

    # POST /api/topics/
    def create(self):
        return Topic.objects.create(
            # self.data is created by restless.
            creator=User.objects.get(username=self.data['user']),
            name=self.data['topic'],
        )

    # PUT /api/topics/<pk>/
    def update(self, pk):
        try:
            topic = Topic.objects.get(id=pk)
        except Topic.DoesNotExist:
            topic = Topic()
        topic.name = self.data['topic']
        topic.creator = User.objects.get(username=self.data['user'])
        topic.save()
        return topic

    # DELETE /api/posts/<pk>/
    def delete(self, pk):
        Topic.objects.get(id=pk).delete()
