import base64
import json
from lxml import html
import requests as rq

class Destiny:
    def __init__(self, key, id: str = "", secret: str = ""):
        if id != "":
            authA = id + ":" + secret
            authEnc = authA.encode('ascii')
            b64 = base64.b64encode(authEnc)
            self.b64A = b64.decode('ascii')
            self.headers = {"X-API-Key": key,
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Authorization": "Basic " + self.b64A}
        else:
            self.headers = {"X-API-Key": key,
                            "Content-Type": "application/x-www-form-urlencoded"}
        self.authHeaders = {"X-API-Key": key,
                            "Content-Type": "application/x-www-form-urlencoded"}
        self.id = ""

    def setCurrentId(self, id):
        self.id = id
        #self.reAuth(self.id)

    def makeApiCall(self, loc, authorized: bool = False):
        return Destiny.apiCall(self, "https://www.bungie.net/Platform" + loc, authorized)

    class apiCall:
        def __init__(self, destiny, url, authorized: bool = False):
            self.url = url
            self.destiny = destiny
            self.authorized = authorized
            self.id = self.destiny.id
        def get(self):
            headers = self.destiny.authHeaders if self.authorized else self.destiny.headers
            with rq.get(self.url, headers=headers) as request:
                if request.status_code == 500:
                    print("User with id " + self.id +" not authorized. Trying to reauthorize...")
                    self.destiny.refreshAuth()
                elif request.status_code != 200:
                    print("Error " + str(request.status_code))
                info = request.json()
                return info["Response"]

    def auth(self, code, refresh: bool = False):
        if not refresh:
            data = {"grant_type": "authorization_code",
                    "code": code}
        else:
           data = {"grant_type": "refresh_token",
                    "refresh_token": code}
        with rq.post("https://www.bungie.net/Platform/App/OAuth/token/", headers=self.headers, data=data) as request:
            if request.status_code != 200:
                print("Error authorizing. Status: " + str(request.status_code))
            else:
                jsonf = request.json()
                newAuth = "Bearer " + jsonf['access_token']
                self.authHeaders["Authorization"] = newAuth
                info = {"headers": self.authHeaders, "refresh": jsonf['refresh_token']}
                with open(self.id + '.json', 'w') as f:
                    json.dump(info, f)

    def reAuth(self, id):
        with open(id + '.json', 'r') as f:
            auth = json.load(f)
            self.authHeaders = auth["headers"]

    def refreshAuth(self):
        with open(self.id + '.json', 'r') as f:
            auth = json.load(f)
            token = auth["refresh"]
        self.auth(token, True)

    def GetMembershipDataForCurrentUser(self):
        call = self.makeApiCall("/User/GetMembershipsForCurrentUser/", True).get()
        return call

    def GetDestinyEntityDefinition(self, entityType, hashIdentifier):
        """
        Returns the static definition of an entity of the given Type and hash identifier. Examine the API Documentation for the Type Names of entities that have their own definitions. Note that the return type will always *inherit from* DestinyDefinition, but the specific type returned will be the requested entity type if it can be found. Please don't use this as a chatty alternative to the Manifest database if you require large sets of data, but for simple and one-off accesses this should be handy.
        """
        call = self.makeApiCall("/Destiny2/Manifest/" + entityType + "/" + str(hashIdentifier)).get()
        return call

    def SearchDestinyPlayer(self, membershipType, displayName):
        """
        Returns a list of Destiny memberships given a full Gamertag or PSN ID. Unless you pass returnOriginalProfile=true, this will return membership information for the users' Primary Cross Save Profile if they are engaged in cross save rather than any original Destiny profile that is now being overridden.
        """
        call = self.makeApiCall("/Destiny2/SearchDestinyPlayer/" + membershipType + "/" + displayName).get()
        return call

    def GetLinkedProfiles(self, membershipType, membershipId):
        """
        Returns a summary information about all profiles linked to the requesting membership type/membership ID that have valid Destiny information. The passed-in Membership Type/Membership ID may be a Bungie.Net membership or a Destiny membership. It only returns the minimal amount of data to begin making more substantive requests, but will hopefully serve as a useful alternative to UserServices for people who just care about Destiny data. Note that it will only return linked accounts whose linkages you are allowed to view.
        """
        call = self.makeApiCall("/Destiny2/" + membershipType + "/Profile/" + membershipId + "/LinkedProfiles/").get()
        return call

    def GetProfile(self, membershipType, membershipId, components):
        """
        Returns Destiny Profile information for the supplied membership.
        """
        call = self.makeApiCall("/Destiny2/" + membershipType + "/Profile/" + membershipId + "/?components=" + components).get()
        return call

    def GetCharacter(self, membershipType, destinyMembershipId, characterId, components):
        """
        Returns character information for the supplied character.
        """
        call = self.makeApiCall("/Destiny2/" + membershipType + "/Profile/" + destinyMembershipId + "/Character/" + characterId + "/?components=" + components).get()
        return call

    def GetClanWeeklyRewardState(self, groupId):
        """
        Returns information on the weekly clan rewards and if the clan has earned them or not. Note that this will always report rewards as not redeemed.
        """
        call = self.makeApiCall("/Destiny2/Clan/" + groupId + "/WeeklyRewardState/").get()
        return call

    def GetItem(self, membershipType, destinyMembershipId, itemInstanceId, components):
        """
        Retrieve the details of an instanced Destiny Item. An instanced Destiny item is one with an ItemInstanceId. Non-instanced items, such as materials, have no useful instance-specific details and thus are not queryable here.
        """
        call = self.makeApiCall("/Destiny2/" + membershipType + "/Profile/" + destinyMembershipId + "/Item/" + itemInstanceId + "/?components=" + components, True).get()
        return call

    def GetVendors(self, membershipType, destinyMembershipId, characterId, components):
        """
        Get currently available vendors from the list of vendors that can possibly have rotating inventory. Note that this does not include things like preview vendors and vendors-as-kiosks, neither of whom have rotating/dynamic inventories. Use their definitions as-is for those.
        """
        call = self.makeApiCall("/Destiny2/" + membershipType + "/Profile/" + destinyMembershipId + "/Character/" + characterId + "/Vendors/?components=" + components, True).get()
        return call

    def GetVendor(self, membershipType, destinyMembershipId, characterId, vendorHash, components):
        """
        Get the details of a specific Vendor.
        """
        call = self.makeApiCall("/Destiny2/" + membershipType + "/Profile/" + destinyMembershipId + "/Character/" + characterId + "/Vendors/" + str(vendorHash) + "/?components=" + components, True).get()
        return call

    def GetPublicVendors(self, components):
        """
        Get items available from vendors where the vendors have items for sale that are common for everyone. If any portion of the Vendor's available inventory is character or account specific, we will be unable to return their data from this endpoint due to the way that available inventory is computed. As I am often guilty of saying: 'It's a long story...'
        """
        call = self.makeApiCall("/Destiny2/Vendors/?components=" + components).get()
        return call
