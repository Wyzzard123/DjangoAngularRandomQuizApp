from rest_framework.exceptions import PermissionDenied


class NoUpdateCreatorMixin:
    """Do not allow users to change the creator of the resource."""
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # Do not allow anyone to change the creator
        if int(request.data['creator']) != instance.creator.id:
            raise PermissionDenied("You do not have permission to update this resource.")

        return super().update(request, *args, **kwargs)

class UserDataBasedOnRequestMixin:
    """
    For create and update (post and put), we will use the self.request.user to manually update the
    data['creator'] field.

    This ensures that we do not need to know the user ID in the database to send API requests.
    """

    def create(self, request, *args, **kwargs):
        # Update creator with the request creator
        request.data.update({'creator': self.request.user.id})
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        request.data.update({'creator': self.request.user.id})
        return super().update(request, *args, **kwargs)
